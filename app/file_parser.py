from abc import ABC, abstractmethod
import os
import io
import logging
from typing import Type, Dict

import PyPDF2
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------
# Base parser interface
# --------------------
class BaseParser(ABC):
    @abstractmethod
    def parse(self, filepath: str) -> str:
        """Parse file content into plain text."""
        raise NotImplementedError


# --------------------
# TXT parser
# --------------------
class TxtParser(BaseParser):
    def parse(self, filepath: str) -> str:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            logger.info(f"Parsed TXT: {filepath}")
            return text
        except Exception as e:
            logger.error(f"Error reading TXT {filepath}: {e}", exc_info=True)
            return ""


# --------------------
# PDF parser (PyPDF2 + OCR fallback)
# --------------------
class PdfParser(BaseParser):
    def parse(self, filepath: str) -> str:
        try:
            content_parts = []

            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)

                # Handle encrypted PDFs
                if getattr(reader, "is_encrypted", False):
                    try:
                        reader.decrypt("")
                    except Exception as e:
                        logger.error(f"Failed to decrypt PDF {filepath}: {e}", exc_info=True)
                        return ""

                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = ""
                    try:
                        page_text = page.extract_text() or ""
                    except Exception:
                        page_text = ""

                    # OCR fallback for pages with no extracted text
                    if not page_text.strip():
                        page_text = self._ocr_page(filepath, page_num)

                    content_parts.append(page_text)

            logger.info(f"Parsed PDF: {filepath}")
            return "\n".join(content_parts).strip()

        except Exception as e:
            logger.error(f"Error processing PDF {filepath}: {e}", exc_info=True)
            return ""

    def _ocr_page(self, filepath: str, page_num: int) -> str:
        try:
            document = fitz.open(filepath)
            page = document.load_page(page_num)
            pix = page.get_pixmap()  # rasterize page
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            document.close()
            return text or ""
        except Exception as e:
            logger.error(f"OCR failed for {filepath} page {page_num}: {e}", exc_info=True)
            return ""


# --------------------
# Parser factory
# --------------------
class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {}

    @classmethod
    def register_parser(cls, extension: str, parser: Type[BaseParser]) -> None:
        cls._parsers[extension.lower().lstrip(".")] = parser

    @classmethod
    def get_parser(cls, extension: str) -> BaseParser:
        ext = extension.lower().lstrip(".")
        parser_cls = cls._parsers.get(ext)
        if not parser_cls:
            raise ValueError(f"No parser found for extension: {extension}")
        return parser_cls()


ParserFactory.register_parser("txt", TxtParser)
ParserFactory.register_parser("pdf", PdfParser)


# --------------------
# FileParser (single interface)
# --------------------
class FileParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.parser = self._get_parser()

    def _get_parser(self) -> BaseParser:
        _, ext = os.path.splitext(self.filepath)
        if not ext:
            raise ValueError("File has no extension.")
        return ParserFactory.get_parser(ext)

    def parse(self) -> str:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
        return self.parser.parse(self.filepath)