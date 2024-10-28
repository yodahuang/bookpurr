## BookPurr

Generate audio books from EPUB files locally, support English and Chinese.

The underlying TTS model is [F5-TTS](https://github.com/SWivid/F5-TTS). Specifically, we use the [MLX implementation](https://github.com/lucasnewman/f5-tts-mlx). This means the code only works on MacOS.

The code does these dirty work for you:
- Handling strange characters in EPUB files.
- Finding the optimal splitting points for long text. (There is a whole file for this. I bashed Claude 3.5 Sonnet for a whole afternoon to get it. On the hindsight, writing it myself would be way faster.)
- Some tests!
- I provide my own voice for reference audio. Not sure if it's a good idea, but hey here it is.

## Usage

```bash
uv run bookpurr $INPUT_EPUB $OUTPUT_DIR
```

I don't have plan to make it a pip package yet.