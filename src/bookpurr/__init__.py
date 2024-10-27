from pathlib import Path

import typer
from epub2txt import epub2txt
from f5_tts_mlx.generate import generate

app = typer.Typer()


def contains_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


@app.command()
def main(epub_path: Path, output_path: Path):
    ch_list = epub2txt(epub_path, outputlist=True)
    tts = F5TTS.from_pretrained("lucasnewman/f5-tts-mlx")
    tts.text_to_speech(text, output_path)


if __name__ == "__main__":
    app()
