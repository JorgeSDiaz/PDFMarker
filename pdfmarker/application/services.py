"""Application services - Use case implementations."""

import os
from pathlib import Path

from pdfmarker.domain.models import Watermark
from pdfmarker.domain.exceptions import WatermarkApplicationError
from pdfmarker.application.ports import PDFRepository, WatermarkRenderer


class WatermarkingServiceImpl:
    """Watermarking use case implementation."""

    def __init__(
        self, pdf_repository: PDFRepository, watermark_renderer: WatermarkRenderer
    ) -> None:
        self._pdf_repo = pdf_repository
        self._renderer = watermark_renderer

    def apply_watermark_to_pdf(self, pdf_path: str, watermark: Watermark) -> str:
        """Apply watermark to PDF file.

        Args:
            pdf_path: Path to the input PDF file
            watermark: Watermark configuration to apply

        Returns:
            Path to the watermarked PDF file

        Raises:
            InvalidPDFError: If PDF is invalid or corrupted
            WatermarkApplicationError: If watermarking fails
        """
        try:
            pdf_doc = self._pdf_repo.read(pdf_path)
            watermark_path = self._renderer.render(
                watermark, (pdf_doc.width, pdf_doc.height)
            )
            output_path = self._generate_output_path(pdf_path)
            self._pdf_repo.merge_watermark(pdf_path, watermark_path, output_path)
            self._cleanup_temp_file(watermark_path)

            return output_path

        except Exception as e:
            if isinstance(e, (WatermarkApplicationError,)):
                raise
            raise WatermarkApplicationError(f"Failed to apply watermark: {e}") from e

    def _generate_output_path(self, input_path: str) -> str:
        path = Path(input_path)
        return str(path.parent / f"{path.stem}_watermarked{path.suffix}")

    def _cleanup_temp_file(self, file_path: str) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
