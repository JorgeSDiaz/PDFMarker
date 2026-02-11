"""Infrastructure adapters - Concrete implementations of ports."""

import os
import tempfile

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from pdfmarker.domain.models import Watermark, PDFDocument, WatermarkType, ImageScaleConfig
from pdfmarker.domain.exceptions import InvalidPDFError, InvalidWatermarkError


class PyPDF2Repository:
    """PDF operations adapter using PyPDF2."""

    def read(self, path: str) -> PDFDocument:
        """Read PDF metadata.

        Args:
            path: Path to the PDF file

        Returns:
            PDFDocument with metadata

        Raises:
            InvalidPDFError: If PDF cannot be read
        """
        try:
            reader = PdfReader(path)

            if len(reader.pages) == 0:
                raise InvalidPDFError(f"PDF has no pages: {path}")

            first_page = reader.pages[0]
            width, height = first_page.mediabox.upper_right

            return PDFDocument(
                width=float(width), height=float(height), pages=len(reader.pages)
            )

        except Exception as e:
            if isinstance(e, InvalidPDFError):
                raise
            raise InvalidPDFError(f"Failed to read PDF '{path}': {e}") from e

    def merge_watermark(
        self, pdf_path: str, watermark_path: str, output_path: str
    ) -> None:
        """Merge watermark PDF with original.

        Args:
            pdf_path: Path to the original PDF
            watermark_path: Path to the watermark PDF
            output_path: Where to save the watermarked PDF

        Raises:
            InvalidPDFError: If PDFs cannot be merged
        """
        try:
            pdf_reader = PdfReader(pdf_path)
            pdf_writer = PdfWriter()

            watermark_reader = PdfReader(watermark_path)
            watermark_page = watermark_reader.pages[0]

            for page in pdf_reader.pages:
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)

            with open(output_path, "wb") as output_file:
                pdf_writer.write(output_file)

        except Exception as e:
            raise InvalidPDFError(f"Failed to merge watermark: {e}") from e


class ReportLabRenderer:
    """Watermark rendering adapter using ReportLab."""

    def _calculate_image_dimensions(
        self,
        image_path: str,
        pdf_dimensions: tuple[float, float],
        scale_config: "ImageScaleConfig | None"
    ) -> tuple[float, float, float, float]:
        """Calculate scaled image dimensions and position.

        Args:
            image_path: Path to the image file
            pdf_dimensions: (width, height) of PDF page in points
            scale_config: Scaling configuration (None = backward compatible 200x200)

        Returns:
            Tuple of (x_offset, y_offset, scaled_width, scaled_height)
        """
        try:
            from PIL import Image

            # Read image to get original dimensions
            with Image.open(image_path) as img:
                orig_width, orig_height = img.size

            # Calculate aspect ratio
            aspect_ratio = orig_width / orig_height
            pdf_width, pdf_height = pdf_dimensions

            # Backward compatibility: use 200x200 if no scale_config
            if scale_config is None:
                return (-100, -100, 200, 200)

            # Get target percentage (None for ORIGINAL preset)
            target_percentage = scale_config.get_percentage()

            if target_percentage is None:
                # ORIGINAL: Use image dimensions in points (1px=1pt)
                target_width = float(orig_width)
                target_height = float(orig_height)
            else:
                # PERCENTAGE: Scale relative to PDF width
                target_width = pdf_width * (target_percentage / 100.0)
                target_height = target_width / aspect_ratio

            # Limit watermark to 95% of PDF dimensions (prevent overflow)
            if target_width > pdf_width * 0.95:
                target_width = pdf_width * 0.95
                target_height = target_width / aspect_ratio

            if target_height > pdf_height * 0.95:
                target_height = pdf_height * 0.95
                target_width = target_height * aspect_ratio

            # Center the watermark (offset from center point)
            x_offset = -target_width / 2
            y_offset = -target_height / 2

            return (x_offset, y_offset, target_width, target_height)

        except FileNotFoundError:
            raise InvalidWatermarkError(f"Image file not found: {image_path}")
        except Exception as e:
            raise InvalidWatermarkError(f"Failed to read image dimensions: {e}")

    def render(self, watermark: Watermark, dimensions: tuple[float, float]) -> str:
        """Render watermark to PDF.

        Args:
            watermark: Watermark configuration
            dimensions: (width, height) in points for the PDF page

        Returns:
            Path to the generated temporary watermark PDF

        Raises:
            InvalidWatermarkError: If watermark cannot be rendered
        """
        try:
            width, height = dimensions

            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(temp_fd)

            canvas_obj = Canvas(temp_path, pagesize=(width, height))

            style = watermark.style
            canvas_obj.setFont(style.font, style.size)
            canvas_obj.setFillColorRGB(0, 0, 0, alpha=style.opacity)
            canvas_obj.saveState()

            canvas_obj.translate(width / 2, height / 2)
            canvas_obj.rotate(style.rotation)

            if watermark.type == WatermarkType.IMAGE:
                # Calculate dimensions with scaling
                x, y, img_width, img_height = self._calculate_image_dimensions(
                    watermark.content,
                    dimensions,
                    watermark.image_scale
                )

                canvas_obj.drawImage(
                    watermark.content,
                    x,
                    y,
                    width=img_width,
                    height=img_height,
                    mask="auto",
                )
            else:
                canvas_obj.drawCentredString(0, 0, watermark.content.upper())

            canvas_obj.restoreState()
            canvas_obj.save()

            return temp_path

        except Exception as e:
            raise InvalidWatermarkError(f"Failed to render watermark: {e}") from e
