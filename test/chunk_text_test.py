import pytest

from bookpurr.chunk_text import split_text


@pytest.mark.parametrize(
    "text, max_words, expected",
    [
        ("Hello, world!", 100, ["Hello, world!"]),
        (
            "This sentence is very long and should be split into chunks.",
            3,
            [
                "This sentence is",
                "very long and",
                "should be split",
                "into chunks.",
            ],
        ),
        (
            "A short paragraph.\n\nFollowed by another paragraph.",
            100,
            ["A short paragraph.\n\nFollowed by another paragraph."],
        ),
        # New tests for punctuation-based splitting
        (
            "First complex sentence; second part of sentence, with a comma, and more details.",
            4,
            [
                "First complex sentence;",
                "second part of sentence,",
                "with a comma,",
                "and more details.",
            ],
        ),
        (
            "Short sentence. Very long sentence that goes on and on and should be split by commas, "
            "first comma part, second comma part, third comma part.",
            5,
            [
                "Short sentence.",
                "Very long sentence that goes",
                "on and on and should",
                "be split by commas,",
                "first comma part,",
                "second comma part,",
                "third comma part.",
            ],
        ),
    ],
)
def test_split_text(text: str, max_words: int, expected: list[str]):
    __tracebackhide__ = True
    assert list(split_text(text, max_words)) == expected
