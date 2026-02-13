"""CLI adapter and composition root."""

import os
from dataclasses import dataclass

from pdfmarker.domain.models import (
    Watermark,
    WatermarkStyle,
    WatermarkType,
    ImageScaleConfig,
    ScalePreset,
)
from pdfmarker.domain.exceptions import (
    InvalidWatermarkError,
    InvalidPDFError,
    WatermarkApplicationError,
)
from pdfmarker.application.services import WatermarkingServiceImpl
from pdfmarker.infrastructure.adapters import PDFRepository, ReportLabRenderer


@dataclass
class UserInput:
    """User input captured from CLI prompts."""

    pdf_path: str
    watermark_type: WatermarkType
    text: str | None
    image_path: str | None
    image_scale: ImageScaleConfig | None = None


class CLIAdapter:
    """Command-line interface adapter."""

    def __init__(self, service: WatermarkingServiceImpl) -> None:
        self._service = service

    def run(self) -> None:
        try:
            user_input = self._get_user_input()

            style = WatermarkStyle()
            content = (
                user_input.text
                if user_input.watermark_type == WatermarkType.TEXT
                else user_input.image_path
            )
            watermark = Watermark(
                type=user_input.watermark_type,
                content=content,
                style=style,
                image_scale=user_input.image_scale,
            )

            output_path = self._service.apply_watermark_to_pdf(
                user_input.pdf_path, watermark
            )
            self._display_success(output_path)

        except (InvalidWatermarkError, InvalidPDFError, WatermarkApplicationError) as e:
            self._display_error(str(e))
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
        except Exception as e:
            self._display_error(f"Unexpected error: {e}")

    def _get_user_input(self) -> UserInput:
        pdf_path = input("Enter base PDF path: ").strip()

        if not pdf_path.endswith(".pdf"):
            pdf_path += ".pdf"

        while True:
            type_input = input("Watermark type (text/image): ").strip().lower()
            if type_input in ("text", "image"):
                watermark_type = (
                    WatermarkType.TEXT if type_input == "text" else WatermarkType.IMAGE
                )
                break
            print("Invalid type. Please enter 'text' or 'image'.")

        text = None
        image_path = None
        image_scale = None

        if watermark_type == WatermarkType.TEXT:
            text = input("Enter watermark text: ").strip()
            if not text:
                raise InvalidWatermarkError("Watermark text cannot be empty")
        else:
            image_path = input("Enter image path: ").strip()
            self._validate_image_path(image_path)
            image_scale = self._get_image_scale_config()

        return UserInput(pdf_path, watermark_type, text, image_path, image_scale)

    def _validate_image_path(self, image_path: str) -> None:
        """Validate that image path exists and is readable.

        Args:
            image_path: Path to the image file

        Raises:
            InvalidWatermarkError: If image path is invalid
        """
        if not image_path:
            raise InvalidWatermarkError("Image path cannot be empty")

        if not os.path.exists(image_path):
            raise InvalidWatermarkError(f"Image file not found: {image_path}")

        if not os.path.isfile(image_path):
            raise InvalidWatermarkError(f"Path is not a file: {image_path}")

        # Validate file extension for early feedback
        valid_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
        if not image_path.lower().endswith(valid_extensions):
            raise InvalidWatermarkError(
                f"Unsupported image format. Supported: {', '.join(valid_extensions)}"
            )

    def _get_image_scale_config(self) -> ImageScaleConfig:
        """Prompt user for image scaling preferences.

        Returns:
            ImageScaleConfig with selected preset/custom value
        """
        print("\nImage Scale Options:")
        print("  1. Small    (20% of PDF width)")
        print("  2. Medium   (40% of PDF width)")
        print("  3. Large    (60% of PDF width)")
        print("  4. Original (actual image size) [default]")
        print("  5. Custom   (specify percentage)")

        while True:
            choice = input("Select scale (1-5) [4]: ").strip() or "4"

            if choice == "1":
                return ImageScaleConfig(preset=ScalePreset.SMALL)
            elif choice == "2":
                return ImageScaleConfig(preset=ScalePreset.MEDIUM)
            elif choice == "3":
                return ImageScaleConfig(preset=ScalePreset.LARGE)
            elif choice == "4":
                return ImageScaleConfig(preset=ScalePreset.ORIGINAL)
            elif choice == "5":
                return self._get_custom_scale()
            else:
                print("Invalid choice. Please enter 1-5.")

    def _get_custom_scale(self) -> ImageScaleConfig:
        """Prompt for custom scaling percentage.

        Returns:
            ImageScaleConfig with CUSTOM preset
        """
        while True:
            try:
                percentage = input("Enter percentage of PDF width (5-100): ").strip()
                value = float(percentage)

                # Domain validation will handle bounds checking
                return ImageScaleConfig(
                    preset=ScalePreset.CUSTOM, custom_percentage=value
                )
            except InvalidWatermarkError as e:
                print(f"✗ {e}")
            except ValueError:
                print("✗ Please enter a valid number.")

    def _display_success(self, output_path: str) -> None:
        print(f"✓ Watermark applied: {output_path}")

    def _display_error(self, message: str) -> None:
        print(f"✗ Error: {message}")


def main() -> None:
    """Composition root - wires all dependencies."""
    pdf_repository = PDFRepository()
    watermark_renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repository, watermark_renderer)
    cli = CLIAdapter(service)
    cli.run()
