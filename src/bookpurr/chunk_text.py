import re
from collections.abc import Iterator
from typing import Pattern


def count_units(text: str) -> int:
    """
    Count units in mixed text:
    - Each Chinese character counts as 1 unit
    - Each non-Chinese word counts as 1 unit
    - Whitespace and newlines are ignored
    - Punctuation marks are not counted
    """
    if not text.strip():
        return 0

    # Split on Chinese characters while preserving spaces and other words
    pattern = r"([\u4e00-\u9fff]|[a-zA-Z0-9]+(?:\.\d+)?(?:[-'][a-zA-Z0-9]+)*)"
    parts = re.findall(pattern, text)
    return len(parts)


def chunk_text(text: str, max_units: int) -> Iterator[str]:
    """
    Split text into chunks using hierarchical approach, preserving semantic units.
    Preserves original whitespace in the output chunks.

    The function follows these steps:
    1. First tries to keep text intact if it's under max_units
    2. If text is too long, attempts to split on punctuation marks in this order:
        - Paragraph breaks (\n\n)
        - Sentence endings (., ?, !)
        - Semicolons and colons (;, :)
        - Commas (,)
    3. If chunks are still too long after punctuation splitting, splits on:
        - Word boundaries for English text
        - Character boundaries for Chinese text

    For each punctuation level:
    - Tries to combine as many segments as possible within max_units limit
    - Only splits when necessary to meet max_units requirement
    """
    text = text.strip()
    if not text:
        return

    if count_units(text) <= max_units:
        yield text
        return

    # Try punctuation-based splitting
    punct_levels: list[str | list[str | Pattern[str]]] = [
        "\n\n",
        [re.compile(r"(?<!\d)[.。]|(?<=[^0-9])[?？!！]")],
        [";", ":", "；", "："],
        [",", "，"],
    ]

    def split_and_merge(
        text: str, punct: str | Pattern[str], max_units: int
    ) -> list[str]:
        """Split text on punctuation and merge greedily"""
        # First get all splits
        if isinstance(punct, Pattern):
            splits = []
            last_pos = 0
            for match in punct.finditer(text):
                split_text = text[last_pos : match.end()].strip()
                if split_text:
                    splits.append(split_text)
                last_pos = match.end()
            if last_pos < len(text):
                splits.append(text[last_pos:].strip())
        else:
            parts = text.split(punct)
            splits = []
            for i, part in enumerate(parts):
                if not part.strip():
                    continue
                # For last part, don't add punctuation
                if i == len(parts) - 1:
                    splits.append(part.strip())
                else:
                    splits.append(part.strip() + punct)

        # Try to merge splits optimally
        result = []
        buffer = []
        buffer_units = 0

        for split in splits:
            split_units = count_units(split)

            # If this split alone exceeds max_units, output buffer and add split directly
            if split_units > max_units:
                if buffer:
                    result.append("".join(buffer))
                    buffer = []
                    buffer_units = 0
                result.append(split)
                continue

            # Try to add to buffer
            test_units = buffer_units + split_units
            if test_units <= max_units:
                buffer.append(split)
                buffer_units = test_units
            else:
                # Output buffer and start new one
                if buffer:
                    result.append("".join(buffer))
                buffer = [split]
                buffer_units = split_units

        # Don't forget remaining buffer
        if buffer:
            result.append("".join(buffer))

        return result

    # Try each punctuation level
    for level in punct_levels:
        if isinstance(level, str):
            splits = split_and_merge(text, level, max_units)
        else:
            splits = [text]
            for punct in level:
                new_splits = []
                for split in splits:
                    if count_units(split) > max_units:
                        new_splits.extend(split_and_merge(split, punct, max_units))
                    else:
                        new_splits.append(split)
                splits = new_splits

        if all(count_units(split) <= max_units for split in splits):
            yield from splits
            return

    # If no punctuation splits worked, fall back to mixed text splitting
    yield from split_mixed_text(text, max_units)


def split_mixed_text(text: str, max_len: int) -> Iterator[str]:
    """Split mixed text into units while preserving word/character boundaries"""
    if not text.strip():
        return

    # First split by language boundaries
    pattern = (
        r"("
        r"[a-zA-Z0-9]+(?:\.\d+)?(?:[-\'][a-zA-Z0-9]+)*(?:\s+[a-zA-Z0-9]+(?:\.\d+)?(?:[-\'][a-zA-Z0-9]+)*)*[.。,，!！?？;；:：]?|"  # English words with decimals
        r"[\u4e00-\u9fff]+[。，！？；：]?"  # Chinese characters with optional punctuation
        r")"
    )
    segments = [s for s in re.findall(pattern, text) if s.strip()]

    for segment in segments:
        # Check if segment is Chinese
        if re.match(r"[\u4e00-\u9fff]", segment):
            # Split Chinese text by character count
            chars = list(re.findall(r"[\u4e00-\u9fff]", segment))
            punct = re.search(r"[。，！？；：]$", segment)

            for i in range(0, len(chars), max_len):
                chunk = chars[i : i + max_len]
                if i + max_len >= len(chars) and punct:
                    yield "".join(chunk) + punct.group()
                else:
                    yield "".join(chunk)
        else:
            # Split English text by words
            words = segment.split()
            current_chunk = []

            for word in words:
                if len(current_chunk) < max_len:
                    current_chunk.append(word)
                else:
                    yield " ".join(current_chunk)
                    current_chunk = [word]

            if current_chunk:
                yield " ".join(current_chunk)
