import re
from collections.abc import Iterator
from typing import Pattern

# Punctuation patterns for text splitting
SENTENCE_END = re.compile(
    r"(?<![0-9])[.。](?![0-9])|[?？!！]"
)  # Don't match decimal points
SEMICOLONS = [";", ":", "；", "："]
COMMAS = [",", "，"]

# Hierarchical punctuation levels for splitting
PUNCT_LEVELS = [
    "\n\n",  # Paragraph breaks
    [SENTENCE_END],  # Sentence endings
    SEMICOLONS,  # Semicolons and colons
    COMMAS,  # Commas
]


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

    pattern = r"([\u4e00-\u9fff]|[a-zA-Z0-9]+(?:\.\d+)?(?:[-'][a-zA-Z0-9]+)*)"
    parts = re.findall(pattern, text)
    return len(parts)


def split_by_punct(text: str, punct: str | Pattern[str]) -> list[str]:
    """Split text by punctuation mark or regex pattern"""
    if isinstance(punct, Pattern):
        splits = []
        last_pos = 0
        for match in punct.finditer(text):
            splits.append(text[last_pos : match.end()])
            last_pos = match.end()
        if last_pos < len(text):
            splits.append(text[last_pos:])
        return [s.strip() for s in splits if s.strip()]

    parts = text.split(punct)
    return [p.strip() + punct for p in parts[:-1] if p.strip()] + [parts[-1].strip()]


def merge_splits(splits: list[str], max_units: int) -> list[str]:
    """Merge splits while respecting max_units limit"""
    result = []
    i = 0

    while i < len(splits):
        # Look ahead to find optimal combination
        best_end = i
        best_combination = splits[i]
        current_units = count_units(splits[i])

        # If this split alone is too big
        if current_units > max_units:
            text_to_split = splits[i]
            subsplits = [text_to_split]

            # Try each punctuation level
            for level in PUNCT_LEVELS:
                if isinstance(level, list):
                    puncts = level
                else:
                    puncts = [level]

                # Try each punctuation mark at this level
                for punct in puncts:
                    if any(count_units(p) > max_units for p in subsplits):
                        new_splits = []
                        for part in subsplits:
                            if count_units(part) > max_units:
                                new_splits.extend(
                                    s.strip()
                                    for s in split_by_punct(part, punct)
                                    if s.strip()
                                )
                            else:
                                new_splits.append(part)
                        subsplits = new_splits

            # Try to combine the subsplits
            current_chunk = []
            current_units = 0

            for split in subsplits:
                split_units = count_units(split)
                if split_units > max_units:
                    if current_chunk:
                        result.append(" ".join(current_chunk))
                    result.extend(split_mixed_text(split, max_units))
                    current_chunk = []
                    current_units = 0
                elif current_units + split_units <= max_units:
                    current_chunk.append(split)
                    current_units += split_units
                else:
                    if current_chunk:
                        result.append(" ".join(current_chunk))
                    current_chunk = [split]
                    current_units = split_units

            if current_chunk:
                result.append(" ".join(current_chunk))

            i += 1
            continue

        # Try to combine with subsequent splits
        for j in range(i + 1, len(splits)):
            test_combination = " ".join(splits[i : j + 1])
            if count_units(test_combination) <= max_units:
                best_combination = test_combination
                best_end = j
            else:
                break

        result.append(best_combination)
        i = best_end + 1

    return result


def split_mixed_text(text: str, max_len: int) -> Iterator[str]:
    """Split mixed text into units while preserving word/character boundaries"""
    if not text.strip():
        return

    pattern = (
        r"("
        r"[a-zA-Z0-9]+(?:\.\d+)?(?:[-\'][a-zA-Z0-9]+)*(?:\s+[a-zA-Z0-9]+(?:\.\d+)?(?:[-\'][a-zA-Z0-9]+)*)*[.。,，!！?？;；:：]?|"
        r"[\u4e00-\u9fff]+[。，！？；：]?"
        r")"
    )
    segments = [s for s in re.findall(pattern, text) if s.strip()]

    for segment in segments:
        if re.match(r"[\u4e00-\u9fff]", segment):
            # Split Chinese text
            chars = list(re.findall(r"[\u4e00-\u9fff]", segment))
            punct = re.search(r"[。，！？；：]$", segment)

            for i in range(0, len(chars), max_len):
                chunk = chars[i : i + max_len]
                if i + max_len >= len(chars) and punct:
                    yield "".join(chunk) + punct.group()
                else:
                    yield "".join(chunk)
        else:
            # Split English text
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


def chunk_text(text: str, max_units: int) -> Iterator[str]:
    """
    Split text into chunks using hierarchical approach, preserving semantic units.

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
    - When splitting is needed, splits at the last possible break point that keeps
      the chunk under max_units (greedy approach)

    Example:
        With max_units=10 and text="a b c, d e f, g h i j k":
        - Won't split at first comma because "a b c" is too small
        - Will split after second comma: "a b c, d e f," (6 units) + "g h i j k" (5 units)
    """
    text = text.strip()
    if not text:
        return

    if count_units(text) <= max_units:
        yield text
        return

    # Try each punctuation level
    for level in PUNCT_LEVELS:
        if isinstance(level, str):
            splits = split_by_punct(text, level)
        else:
            splits = [text]
            for punct in level:
                new_splits = []
                for part in splits:
                    new_splits.extend(split_by_punct(part, punct))
                splits = new_splits

        if len(splits) > 1:
            merged = merge_splits(splits, max_units)
            if all(count_units(chunk) <= max_units for chunk in merged):
                yield from merged
                return

    # Fallback to word/character splitting
    yield from split_mixed_text(text, max_units)
