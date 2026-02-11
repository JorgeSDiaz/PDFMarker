"""Domain models - Entities and Value Objects."""

from dataclasses import dataclass
from enum import Enum

from pdfmarker.domain.exceptions import InvalidWatermarkError


class WatermarkType(Enum):
    TEXT = "text"
    IMAGE = "image"


class ScalePreset(Enum):
    """Preset scaling options for image watermarks."""
    SMALL = "small"      # 20% of PDF width
    MEDIUM = "medium"    # 40% of PDF width
    LARGE = "large"      # 60% of PDF width
    ORIGINAL = "original"  # Original image size (1px=1pt, limited to 95% of PDF)
    CUSTOM = "custom"    # User-defined percentage


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


@dataclass(frozen=True)
class ImageScaleConfig:
    """Image-specific watermark scaling configuration.

    Handles scaling relative to PDF dimensions with aspect ratio preservation.
    """
    preset: ScalePreset = ScalePreset.ORIGINAL
    custom_percentage: float | None = None  # Only used when preset=CUSTOM

    def __post_init__(self) -> None:
        # Validation: CUSTOM preset requires custom_percentage
        if self.preset == ScalePreset.CUSTOM:
            if self.custom_percentage is None:
                raise InvalidWatermarkError(
                    "custom_percentage required when using CUSTOM preset"
                )
            if not 5 <= self.custom_percentage <= 100:
                raise InvalidWatermarkError(
                    f"custom_percentage must be 5-100, got {self.custom_percentage}"
                )
        # Validation: custom_percentage only valid with CUSTOM
        elif self.custom_percentage is not None:
            raise InvalidWatermarkError(
                "custom_percentage only valid with CUSTOM preset"
            )

    def get_percentage(self) -> float | None:
        """Get scaling percentage based on preset.

        Returns:
            Percentage of PDF width (5-100), or None for ORIGINAL preset
        """
        if self.preset == ScalePreset.SMALL:
            return 20.0
        elif self.preset == ScalePreset.MEDIUM:
            return 40.0
        elif self.preset == ScalePreset.LARGE:
            return 60.0
        elif self.preset == ScalePreset.ORIGINAL:
            return None  # Signal to use original dimensions
        else:
            return self.custom_percentage


@dataclass
class Watermark:
    type: WatermarkType
    content: str
    style: WatermarkStyle
    image_scale: ImageScaleConfig | None = None  # Only for IMAGE type

    def __post_init__(self) -> None:
        if not self.content:
            raise InvalidWatermarkError("Watermark content cannot be empty")

        if self.image_scale is not None and self.type != WatermarkType.IMAGE:
            raise InvalidWatermarkError(
                "image_scale only valid for IMAGE watermarks"
            )


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
