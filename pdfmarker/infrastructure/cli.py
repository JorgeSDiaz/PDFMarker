"""CLI adapter and composition root."""

import os
from dataclasses import dataclass

from pdfmarker.domain.models import Watermark, WatermarkStyle, WatermarkType
from pdfmarker.domain.exceptions import (
    InvalidWatermarkError,
    InvalidPDFError,
    WatermarkApplicationError,
)
from pdfmarker.application.services import WatermarkingServiceImpl
from pdfmarker.infrastructure.adapters import PyPDF2Repository, ReportLabRenderer


@dataclass
class UserInput:
    """User input captured from CLI prompts."""
    pdf_path: str
    watermark_type: WatermarkType
    text: str | None
    image_path: str | None


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
                style=style
            )

            output_path = self._service.apply_watermark_to_pdf(user_input.pdf_path, watermark)
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

        # Prompt for type with validation loop
        while True:
            type_input = input("Watermark type (text/image): ").strip().lower()
            if type_input in ("text", "image"):
                watermark_type = (
                    WatermarkType.TEXT if type_input == "text" else WatermarkType.IMAGE
                )
                break
            print("Invalid type. Please enter 'text' or 'image'.")

        # Get content based on type
        text = None
        image_path = None

        if watermark_type == WatermarkType.TEXT:
            text = input("Enter watermark text: ").strip()
            if not text:
                raise InvalidWatermarkError("Watermark text cannot be empty")
        else:
            image_path = input("Enter image path: ").strip()
            self._validate_image_path(image_path)

        return UserInput(pdf_path, watermark_type, text, image_path)

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
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        if not image_path.lower().endswith(valid_extensions):
            raise InvalidWatermarkError(
                f"Unsupported image format. Supported: {', '.join(valid_extensions)}"
            )

    def _display_success(self, output_path: str) -> None:
        print(f"✓ Watermark applied: {output_path}")

    def _display_error(self, message: str) -> None:
        print(f"✗ Error: {message}")


def main() -> None:
    """Composition root - wires all dependencies."""
    pdf_repository = PyPDF2Repository()
    watermark_renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repository, watermark_renderer)
    cli = CLIAdapter(service)
    cli.run()
