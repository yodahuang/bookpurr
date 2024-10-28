# Inspired from t5_tts_mlx.generate, with chunked generation, removal of debugging info, and changed output format.

import logging
import pkgutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import mlx.core as mx
import numpy as np
import soundfile as sf
from f5_tts_mlx.cfm import F5TTS
from f5_tts_mlx.utils import convert_char_to_pinyin
from rich.progress import Progress

from bookpurr.chunk_text import chunk_text

SAMPLE_RATE = 24_000
TARGET_RMS = 0.1


def contains_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def generate(
    generation_text: str,
    model: F5TTS | None = None,
    model_name: str = "lucasnewman/f5-tts-mlx",
    ref_audio_path: str | None = None,
    ref_audio_text: str | None = None,
    steps: int = 32,
    method: Literal["euler", "midpoint"] = "euler",
    cfg_strength: float = 2.0,
    sway_sampling_coef: float = -1.0,
    speed: float = 0.8,  # used as part of the duration heuristic
    seed: int | None = None,
) -> Iterator[mx.array]:
    if model is None:
        f5tts = F5TTS.from_pretrained(model_name)
    else:
        f5tts = model

    if ref_audio_path is None:
        is_cn_book = contains_chinese(generation_text)
        if is_cn_book:
            data = pkgutil.get_data("bookpurr", "data/yanda-en.wav")
            ref_audio_text = "Some call me nature, others call me mother nature."
        else:
            data = pkgutil.get_data("bookpurr", "data/yanda-cn.wav")
            ref_audio_text = "有些人叫我自然，有些人叫我自然母亲。"
        if data is None:
            raise ValueError("Reference audio not found")

        # write to a temp file
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_ref_audio_file:
            tmp_ref_audio_file.write(data)
            tmp_ref_audio_file.flush()
            audio, sr = sf.read(tmp_ref_audio_file.name)
    else:
        # load reference audio
        audio, sr = sf.read(ref_audio_path)
        if sr != SAMPLE_RATE:
            raise ValueError("Reference audio must have a sample rate of 24kHz")

    audio = mx.array(audio)
    ref_audio_duration = audio.shape[0] / SAMPLE_RATE
    logging.info(f"Got reference audio with duration: {ref_audio_duration:.2f} seconds")

    rms = mx.sqrt(mx.mean(mx.square(audio)))
    if rms < TARGET_RMS:
        audio = audio * TARGET_RMS / rms

    text_chunks = list(chunk_text(generation_text, max_units=50))

    with Progress() as progress:
        for text_chunk in progress.track(text_chunks, description="Generating audio"):
            progress.print(text_chunk)
            # TODO: Pad with space and batch process.
            # See https://github.com/SWivid/F5-TTS/issues/264
            batch = [ref_audio_text + " " + text_chunk]
            if contains_chinese(batch):
                text = convert_char_to_pinyin(batch)
            else:
                text = batch

            wave, _ = f5tts.sample(
                mx.expand_dims(audio, axis=0),
                text=text,
                duration=None,
                steps=steps,
                method=method,
                speed=speed,
                cfg_strength=cfg_strength,
                sway_sampling_coef=sway_sampling_coef,
                seed=seed,
            )

            # trim the reference audio
            wave = wave[audio.shape[0] :]
            generated_duration = wave.shape[0] / SAMPLE_RATE

            progress.print(f"Generated {generated_duration:.2f} seconds of audio.")
            yield wave


def save_audio(waves: list[mx.array], output_path: Path) -> None:
    with output_path.open("wb") as output:
        sf.write(output, np.array(mx.concatenate(waves, axis=0)), SAMPLE_RATE)
