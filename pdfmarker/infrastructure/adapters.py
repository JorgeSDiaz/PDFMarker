"""Infrastructure adapters - Concrete implementations of ports."""

import os
import tempfile

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from pdfmarker.domain.models import Watermark, PDFDocument, WatermarkType
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
                canvas_obj.drawImage(
                    watermark.content,
                    -100,
                    -100,
                    width=200,
                    height=200,
                    mask="auto",
                )
            else:
                canvas_obj.drawCentredString(0, 0, watermark.content.upper())

            canvas_obj.restoreState()
            canvas_obj.save()

            return temp_path

        except Exception as e:
            raise InvalidWatermarkError(f"Failed to render watermark: {e}") from e
