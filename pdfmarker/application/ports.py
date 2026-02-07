"""Application ports - Hexagonal architecture boundaries."""

from typing import Protocol

from pdfmarker.domain.models import Watermark, PDFDocument


class WatermarkingService(Protocol):
    """Inbound port - What the application offers to the outside world."""

    def apply_watermark_to_pdf(self, pdf_path: str, watermark: Watermark) -> str:
        """Apply watermark to PDF and return output path.

        Args:
            pdf_path: Path to the input PDF file
            watermark: Watermark configuration to apply

        Returns:
            Path to the watermarked PDF file

        Raises:
            InvalidPDFError: If PDF is invalid or corrupted
            WatermarkApplicationError: If watermarking fails
        """
        ...


class PDFRepository(Protocol):
    """Outbound port - PDF operations abstraction."""

    def read(self, path: str) -> PDFDocument:
        """Read PDF metadata.

        Args:
            path: Path to the PDF file

        Returns:
            PDFDocument with metadata

        Raises:
            InvalidPDFError: If PDF cannot be read or is invalid
        """
        ...

    def merge_watermark(
        self, pdf_path: str, watermark_path: str, output_path: str
    ) -> None:
        """Merge watermark PDF with original PDF.

        Args:
            pdf_path: Path to the original PDF
            watermark_path: Path to the watermark PDF
            output_path: Where to save the watermarked PDF

        Raises:
            InvalidPDFError: If PDFs cannot be merged
        """
        ...


class WatermarkRenderer(Protocol):
    """Outbound port - Watermark rendering abstraction."""

    def render(self, watermark: Watermark, dimensions: tuple[float, float]) -> str:
        """Render watermark to a PDF file.

        Args:
            watermark: Watermark configuration
            dimensions: (width, height) in points for the PDF page

        Returns:
            Path to the generated watermark PDF

        Raises:
            InvalidWatermarkError: If watermark cannot be rendered
        """
        ...
