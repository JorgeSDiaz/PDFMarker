"""Domain models - Entities and Value Objects."""

from dataclasses import dataclass
from enum import Enum

from pdfmarker.domain.exceptions import InvalidWatermarkError


class WatermarkType(Enum):
    TEXT = "text"
    IMAGE = "image"


@dataclass(frozen=True)
class WatermarkStyle:
    font: str = "Helvetica"
    size: int = 28
    opacity: float = 0.3
    rotation: int = 45

    def __post_init__(self) -> None:
        if not 0 <= self.opacity <= 1:
            raise InvalidWatermarkError(
                f"Opacity must be between 0 and 1, got {self.opacity}"
            )

        if not 0 <= self.rotation <= 360:
            raise InvalidWatermarkError(
                f"Rotation must be between 0 and 360 degrees, got {self.rotation}"
            )

        if self.size <= 0:
            raise InvalidWatermarkError(
                f"Font size must be positive, got {self.size}"
            )


@dataclass
class Watermark:
    type: WatermarkType
    content: str
    style: WatermarkStyle

    def __post_init__(self) -> None:
        if not self.content:
            raise InvalidWatermarkError("Watermark content cannot be empty")


@dataclass
class PDFDocument:
    width: float
    height: float
    pages: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise InvalidWatermarkError(
                f"PDF dimensions must be positive, got {self.width}x{self.height}"
            )

        if self.pages <= 0:
            raise InvalidWatermarkError(
                f"PDF must have at least one page, got {self.pages}"
            )
