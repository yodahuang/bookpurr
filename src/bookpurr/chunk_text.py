import re
from collections.abc import Iterator
from typing import Pattern


def chunk_text(text: str, max_words: int) -> Iterator[str]:
    """
    Split text into chunks, each containing no more than max_words words.

    The function uses a hierarchical approach to splitting:
    1. First tries to keep text intact if it's under max_words
    2. If text is too long, attempts to split on punctuation marks in this order:
        - Paragraph breaks (\n\n)
        - Sentence endings (., ?, !)
        - Semicolons and colons (;, :)
        - Commas (,)
    3. If chunks are still too long after punctuation splitting, splits on word boundaries

    For each punctuation level:
    - Paragraph breaks (\n\n) are removed from output
    - All other punctuation marks are kept with their preceding text
    - Chunks under max_words are not split further

    Args:
        text: Input text to split
        max_words: Maximum number of words per chunk (default: 100)

    Returns:
        Iterator of text chunks, each containing max_words or fewer words

    Example:
        >>> list(split_text("Short text. Very, very long text.", max_words=2))
        ['Short text.', 'Very,', 'very long text.']
    """
    punct_levels: list[str | list[str | Pattern[str]]] = [
        "\n\n",
        [
            re.compile(r"(?<!\d)\.|(?<=[^0-9])[?!]")
        ],  # Don't match decimal points in numbers
        [";", ":"],
        [","],
    ]

    def count_words(text: str) -> int:
        return len(text.split())

    def merge_chunks(splits: list[str]) -> Iterator[str]:
        current_text: str = ""
        current_words: int = 0

        for split_text in splits:
            split_words = count_words(split_text)
            if current_words + split_words <= max_words:
                current_text += split_text
                current_words += split_words
            else:
                if current_text:
                    yield current_text.strip()
                current_text = split_text
                current_words = split_words

        if current_text:
            yield current_text.strip()

    # Initial setup
    chunks: list[str] = [text]

    # Try each punctuation level until we get small enough chunks
    for level in punct_levels:
        if isinstance(level, str):
            level = [level]

        new_chunks: list[str] = []
        for chunk in chunks:
            if count_words(chunk) <= max_words:
                new_chunks.append(chunk)
                continue

            # Split on current punctuation level
            current = chunk
            splits: list[str] = []

            for punct in level:
                if isinstance(punct, Pattern):
                    parts = punct.split(current)
                    current = parts[-1]
                    for part in parts[:-1]:
                        # Get the actual punctuation mark that was matched (. ? or !)
                        splits.append(
                            part.strip() + "."
                        )  # We know it's always a period in this case
                else:
                    parts = current.split(punct)
                    current = parts[-1]
                    for part in parts[:-1]:
                        if punct == "\n\n":
                            splits.append(part.strip())  # Don't append \n\n
                        else:
                            splits.append(
                                part.strip() + punct
                            )  # Keep other punctuation

            # Don't forget to append the last part with its punctuation if it exists
            if current.strip():
                splits.append(current.strip())

            new_chunks.extend(merge_chunks(splits))

        chunks = new_chunks
        if all(count_words(chunk) <= max_words for chunk in chunks):
            break

    # Final word-based split for any remaining long chunks
    for chunk in chunks:
        if count_words(chunk) > max_words:
            words = chunk.split()
            current_chunk: list[str] = []

            for word in words:
                if len(current_chunk) < max_words:
                    current_chunk.append(word)
                else:
                    yield " ".join(current_chunk)
                    current_chunk = [word]

            if current_chunk:
                yield " ".join(current_chunk)
        else:
            yield chunk.strip()
