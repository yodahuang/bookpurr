import logging
import unicodedata

import chardet
from ebooklib.epub import EpubBook
from lxml import etree


def get_epub_encoding(epub: EpubBook) -> str | None:
    for item in epub.items:
        if item.media_type == "application/xhtml+xml":
            if not item.content:
                continue

            parser = etree.XMLParser(recover=True)
            try:
                tree = etree.fromstring(item.content, parser)
            except (etree.XMLSyntaxError, etree.ParseError):
                continue

            if hasattr(tree, "docinfo") and tree.docinfo.encoding:
                return tree.docinfo.encoding.lower()

            meta_tags = tree.xpath("//meta[@charset]")
            if meta_tags:
                return meta_tags[0].get("charset").lower()

            meta_content_type = tree.xpath('//meta[@http-equiv="Content-Type"]')
            if meta_content_type:
                content = meta_content_type[0].get("content")
                if "charset=" in content:
                    return content.split("charset=")[1].strip().lower()

    return None


def fix_encoding(text: str) -> str:
    if not text:
        return text

    # First convert to bytes using a safe encoding
    byte_string = text.encode("latin1")

    # Detect the likely encoding
    detection = chardet.detect(byte_string)
    if detection["confidence"] > 0.7:  # Reasonable confidence threshold
        try:
            logging.info(f"Detected encoding: {detection['encoding']}")
            decoded = byte_string.decode(detection["encoding"])
            if decoded != text:  # Only return if we actually fixed something
                return decoded
        except UnicodeError:
            logging.exception()
            return text


def fix_encoding_simple(text: str) -> str:
    if not text:
        return text

    # Replace common mojibake patterns
    replacements = {
        "â\x80\x99": "'",
        "â\x80\x98": "'",
        "â\x80\x9c": '"',
        "â\x80\x9d": '"',
        "â\x80\x93": "–",
        "â\x80\x94": "—",
        "Â": "",
        "\x80": "",
        "\x99": "",
    }

    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    return text
