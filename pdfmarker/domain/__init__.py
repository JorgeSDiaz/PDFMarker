"""Domain layer - Pure business logic with zero external dependencies."""

from pdfmarker.domain.models import (
    WatermarkType,
    WatermarkStyle,
    Watermark,
    PDFDocument,
)
from pdfmarker.domain.exceptions import (
    InvalidWatermarkError,
    InvalidPDFError,
    WatermarkApplicationError,
)

__all__ = [
    "WatermarkType",
    "WatermarkStyle",
    "Watermark",
    "PDFDocument",
    "InvalidWatermarkError",
    "InvalidPDFError",
    "WatermarkApplicationError",
]
