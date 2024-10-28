import pytest

from bookpurr.chunk_text import chunk_text


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
        # Test that we don't split unnecessarily
        (
            "Short text. Another short text.",
            5,
            ["Short text. Another short text."],  # Should stay as one chunk
        ),
        # Test handling of spaces and newlines in Chinese
        (
            "这是 第一段。\n这是第二段。",  # Extra spaces and newlines
            100,
            ["这是 第一段。\n这是第二段。"],  # Preserve original spacing
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
        # Test greedy chunking - should combine as much as possible within max_units
        # Not exactly what I want, but Claude 3.5 is just dumb.
        (
            "Short sentence. Very long sentence that goes on and on and should be split by commas, "
            "first comma part, second comma part, third comma part.",
            10,
            [
                "Short sentence.",
                "Very long sentence that goes on and on and should",
                "be split by commas,",
                "first comma part, second comma part, third comma part.",
            ],
        ),
        # Test for numbers with decimal points
        (
            "An average human lives for 80.79 years. Then they die.",
            4,
            [
                "An average human lives",
                "for 80.79 years.",
                "Then they die.",
            ],
        ),
        # Pure Chinese test cases
        (
            "我能吞下玻璃而不伤身体。",
            3,
            ["我能吞", "下玻璃", "而不伤", "身体。"],
        ),
        # Mixed Chinese/English test cases - split on language change and by character limit
        (
            "Hello World 你好世界",
            2,
            ["Hello World", "你好", "世界"],
        ),
        (
            "Chapter 1 第一章。The story begins。",
            3,
            ["Chapter 1", "第一章。", "The story begins。"],
        ),
        (
            "这是测试。Test text。这是中文。",
            3,
            ["这是测", "试。", "Test text。", "这是中", "文。"],
        ),
        (
            "The cat and dog 猫和狗",
            3,
            ["The cat and", "dog", "猫和狗"],
        ),
        (
            "Chapter 1\n\n第一章\n\nThe story\n\n故事",
            3,
            ["Chapter 1\n\n", "第一章\n\n", "The story\n\n", "故事"],
        ),
        (
            "This is very long 这是非常长的句子",
            4,
            ["This is very long", "这是非常", "长的句子"],
        ),
    ],
)
def test_split_text(text: str, max_words: int, expected: list[str]):
    __tracebackhide__ = True
    assert list(chunk_text(text, max_words)) == expected
