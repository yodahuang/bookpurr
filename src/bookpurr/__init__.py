import html
import logging
from pathlib import Path

import typer
from epub2txt import epub2txt
from f5_tts_mlx.cfm import F5TTS

from bookpurr.epub_utils import fix_encoding_simple
from bookpurr.generate import contains_chinese, generate, save_audio

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def main(
    epub_path: Path,
    output_dir: Path,
    word_limit: int | None = None,
    chapter: int | None = None,
    ref_audio_path: Path | None = None,
    ref_audio_text: str | None = None,
):
    logging.basicConfig(level=logging.INFO)

    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    chapters: list[str] = [
        fix_encoding_simple(chapter) for chapter in epub2txt(epub_path, outputlist=True)
    ]

    if chapter is not None:
        chapters = [chapters[chapter]]

    if word_limit is not None:
        allowed_word_count = word_limit
        for i, chapter in enumerate(chapters):
            if contains_chinese(chapter):
                # For Chinese text, count characters
                chapter_words = list(chapter)
            else:
                # For non-Chinese text, split by words
                chapter_words = chapter.split()

            chapter_word_count = len(chapter_words)
            if chapter_word_count > allowed_word_count:
                # Join back the allowed number of words/chars
                chapters[i] = (
                    "".join(chapter_words[:allowed_word_count])
                    if contains_chinese(chapter)
                    else " ".join(chapter_words[:allowed_word_count])
                )
                chapters = chapters[: i + 1]
                break
            allowed_word_count -= chapter_word_count

    model = F5TTS.from_pretrained("lucasnewman/f5-tts-mlx")

    for i, chapter in enumerate(chapters):
        logging.info(f"Generating chapter {i}")
        waves = list(
            generate(
                chapter,
                model=model,
                ref_audio_path=ref_audio_path,
                ref_audio_text=ref_audio_text,
                speed=0.8,
            )
        )
        save_audio(waves, output_dir / f"chapter{i}.wav")


if __name__ == "__main__":
    app()
