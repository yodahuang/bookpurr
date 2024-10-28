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

    # Try punctuation-based splitting in order
    punct_levels: list[str | list[str | Pattern[str]]] = [
        "\n\n",
        [re.compile(r"(?<!\d)[.。]|(?<=[^0-9])[?？!！]")],  # Don't match decimal points
        [";", ":", "；", "："],
        [",", "，"],
    ]

    def split_by_punct(text: str, punct: str | Pattern[str]) -> list[str]:
        if isinstance(punct, Pattern):
            splits = []
            last_pos = 0
            for match in punct.finditer(text):
                splits.append(text[last_pos : match.end()])
                last_pos = match.end()
            if last_pos < len(text):
                splits.append(text[last_pos:])
            return [s.strip() for s in splits if s.strip()]
        else:
            parts = text.split(punct)
            return [p.strip() + punct for p in parts[:-1] if p.strip()] + [
                parts[-1].strip()
            ]

    def merge_greedily(splits: list[str]) -> list[str]:
        """Try to combine as many splits as possible while staying under max_units"""
        print("\nTrying to merge splits:", splits)
        result = []
        i = 0
        while i < len(splits):
            # Try to find the longest sequence of splits that fits in max_units
            current_units = 0
            j = i
            while j < len(splits):
                next_units = count_units(splits[j])
                print(f"  Checking split {j}: '{splits[j]}' ({next_units} units)")
                if current_units + next_units <= max_units:
                    current_units += next_units
                    print(f"    Can add it. Current total: {current_units}")
                    j += 1
                else:
                    print(f"    Would exceed max_units ({max_units})")
                    break

            # If we found a valid sequence, add it
            if j > i:
                # Join with spaces for readability
                merged = " ".join(s.strip() for s in splits[i:j])
                print(f"  Adding merged chunk: '{merged}' ({current_units} units)")
                result.append(merged)
                i = j
            else:
                # If even a single split is too big, pass it through
                print(f"  Split too big, passing through: '{splits[i]}'")
                result.append(splits[i])
                i += 1

        print("Merge result:", result)
        return result

    def split_and_merge_recursively(
        text: str, max_units: int, level_index: int = 0
    ) -> list[str]:
        """Split text recursively and merge greedily"""
        print(f"\nRecursive call at level {level_index} with text: '{text}'")

        # Base case: text fits in max_units
        if count_units(text) <= max_units:
            return [text]

        # If we've tried all punctuation levels, fall back to word/character splitting
        if level_index >= len(punct_levels):
            return list(split_mixed_text(text, max_units))

        # Get current punctuation level
        level = punct_levels[level_index]
        if isinstance(level, str):
            level = [level]

        # Try splitting at current punctuation level
        splits = []
        current = text
        for punct in level:
            if isinstance(punct, Pattern):
                matches = list(punct.finditer(current))
                if matches:
                    last_pos = 0
                    for match in matches:
                        splits.append(current[last_pos : match.end()].strip())
                        last_pos = match.end()
                    current = (
                        current[last_pos:].strip() if last_pos < len(current) else ""
                    )
            else:
                parts = current.split(punct)
                current = parts[-1].strip()
                splits.extend(
                    part.strip() + punct for part in parts[:-1] if part.strip()
                )

        if current:
            splits.append(current)

        if not splits:
            # No splits at this level, try next level
            return split_and_merge_recursively(text, max_units, level_index + 1)

        # Try to combine splits greedily
        result = []
        i = 0
        while i < len(splits):
            # Look ahead to find maximum valid combination
            best_end = i
            combined = splits[i]
            units = count_units(splits[i])

            for j in range(i + 1, len(splits)):
                next_units = count_units(splits[j])
                if units + next_units <= max_units:
                    combined = combined + " " + splits[j]
                    units += next_units
                    best_end = j
                else:
                    break

            if units > max_units:
                # If single split is too big, recurse to next level
                result.extend(
                    split_and_merge_recursively(splits[i], max_units, level_index + 1)
                )
                i += 1
            else:
                # Add the best combination we found
                result.append(combined)
                i = best_end + 1

        return result

    # Start the recursive process
    yield from split_and_merge_recursively(text, max_units)


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
