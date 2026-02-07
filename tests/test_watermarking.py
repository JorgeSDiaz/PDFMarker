"""Tests for watermarking functionality.

Tests organized by layer:
- Domain: Models and validation
- Application: Service orchestration with mocks
- Infrastructure: Adapter implementations (optional)
"""

import pytest
from unittest.mock import Mock

from pdfmarker.domain.models import (
    WatermarkType,
    WatermarkStyle,
    Watermark,
    PDFDocument,
)
from pdfmarker.domain.exceptions import InvalidWatermarkError
from pdfmarker.application.services import WatermarkingServiceImpl
from pdfmarker.application.ports import PDFRepository, WatermarkRenderer
from pdfmarker.infrastructure.cli import CLIAdapter


# ============================================================================
# Domain Layer Tests - Pure business logic
# ============================================================================


class TestWatermarkStyle:
    """Test WatermarkStyle value object validation."""

    def test_default_values(self):
        """Test default styling values."""
        style = WatermarkStyle()
        assert style.font == "Helvetica"
        assert style.size == 28
        assert style.opacity == 0.3
        assert style.rotation == 45

    def test_valid_custom_values(self):
        """Test custom valid values."""
        style = WatermarkStyle(opacity=0.5, rotation=90, size=40)
        assert style.opacity == 0.5
        assert style.rotation == 90
        assert style.size == 40

    def test_opacity_validation_too_high(self):
        """Test opacity validation rejects values > 1."""
        with pytest.raises(InvalidWatermarkError, match="Opacity must be between 0 and 1"):
            WatermarkStyle(opacity=1.5)

    def test_opacity_validation_negative(self):
        """Test opacity validation rejects negative values."""
        with pytest.raises(InvalidWatermarkError, match="Opacity must be between 0 and 1"):
            WatermarkStyle(opacity=-0.1)

    def test_rotation_validation_too_high(self):
        """Test rotation validation rejects values > 360."""
        with pytest.raises(InvalidWatermarkError, match="Rotation must be between 0 and 360"):
            WatermarkStyle(rotation=400)

    def test_size_validation_negative(self):
        """Test size validation rejects non-positive values."""
        with pytest.raises(InvalidWatermarkError, match="Font size must be positive"):
            WatermarkStyle(size=-10)

    def test_immutability(self):
        """Test that WatermarkStyle is immutable (frozen)."""
        style = WatermarkStyle()
        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            style.opacity = 0.5


class TestWatermark:
    """Test Watermark entity."""

    def test_text_watermark_creation(self):
        """Test creating a text watermark."""
        style = WatermarkStyle()
        watermark = Watermark(type=WatermarkType.TEXT, content="CONFIDENTIAL", style=style)

        assert watermark.type == WatermarkType.TEXT
        assert watermark.content == "CONFIDENTIAL"
        assert watermark.style.opacity == 0.3

    def test_empty_content_validation(self):
        """Test that empty content is rejected."""
        style = WatermarkStyle()
        with pytest.raises(InvalidWatermarkError, match="content cannot be empty"):
            Watermark(type=WatermarkType.TEXT, content="", style=style)


class TestPDFDocument:
    """Test PDFDocument entity."""

    def test_valid_pdf_document(self):
        """Test creating a valid PDF document."""
        doc = PDFDocument(width=612.0, height=792.0, pages=5)
        assert doc.width == 612.0
        assert doc.height == 792.0
        assert doc.pages == 5

    def test_invalid_dimensions(self):
        """Test validation rejects invalid dimensions."""
        with pytest.raises(InvalidWatermarkError, match="dimensions must be positive"):
            PDFDocument(width=-100, height=200, pages=1)

    def test_invalid_page_count(self):
        """Test validation rejects invalid page count."""
        with pytest.raises(InvalidWatermarkError, match="must have at least one page"):
            PDFDocument(width=612.0, height=792.0, pages=0)


# ============================================================================
# Application Layer Tests - Service with mocked ports
# ============================================================================


class TestWatermarkingService:
    """Test WatermarkingServiceImpl with mocked dependencies."""

    def test_apply_watermark_success(self):
        """Test successful watermark application."""
        # Arrange - Create mocks
        mock_pdf_repo = Mock(spec=PDFRepository)
        mock_renderer = Mock(spec=WatermarkRenderer)

        # Configure mocks
        mock_pdf_repo.read.return_value = PDFDocument(
            width=612.0, height=792.0, pages=1
        )
        mock_renderer.render.return_value = "/tmp/watermark.pdf"

        # Create service with mocked dependencies
        service = WatermarkingServiceImpl(mock_pdf_repo, mock_renderer)

        # Create watermark
        style = WatermarkStyle()
        watermark = Watermark(
            type=WatermarkType.TEXT, content="CONFIDENTIAL", style=style
        )

        # Act
        result = service.apply_watermark_to_pdf("input.pdf", watermark)

        # Assert
        assert result == "input_watermarked.pdf"
        mock_pdf_repo.read.assert_called_once_with("input.pdf")
        mock_renderer.render.assert_called_once_with(watermark, (612.0, 792.0))
        mock_pdf_repo.merge_watermark.assert_called_once()

    def test_generate_output_path(self):
        """Test output path generation."""
        mock_pdf_repo = Mock(spec=PDFRepository)
        mock_renderer = Mock(spec=WatermarkRenderer)
        service = WatermarkingServiceImpl(mock_pdf_repo, mock_renderer)

        # Test various input paths
        assert service._generate_output_path("document.pdf") == "document_watermarked.pdf"
        assert service._generate_output_path("/path/to/doc.pdf") == "/path/to/doc_watermarked.pdf"


# ============================================================================
# Infrastructure Layer Tests - CLI Adapter
# ============================================================================


class TestCLIAdapter:
    """Test CLI user input handling and validation."""

    def test_validate_image_path_valid(self, tmp_path):
        """Test validation passes for valid image file."""
        image = tmp_path / "test.png"
        image.touch()

        cli = CLIAdapter(Mock())
        cli._validate_image_path(str(image))  # Should not raise

    def test_validate_image_path_not_found(self):
        """Test validation rejects non-existent path."""
        cli = CLIAdapter(Mock())
        with pytest.raises(InvalidWatermarkError, match="not found"):
            cli._validate_image_path("/nonexistent/image.png")

    def test_validate_image_path_is_directory(self, tmp_path):
        """Test validation rejects directory path."""
        cli = CLIAdapter(Mock())
        with pytest.raises(InvalidWatermarkError, match="not a file"):
            cli._validate_image_path(str(tmp_path))

    def test_validate_image_path_invalid_extension(self, tmp_path):
        """Test validation rejects invalid file extension."""
        invalid = tmp_path / "file.txt"
        invalid.touch()

        cli = CLIAdapter(Mock())
        with pytest.raises(InvalidWatermarkError, match="Unsupported image format"):
            cli._validate_image_path(str(invalid))

    def test_validate_image_path_empty(self):
        """Test validation rejects empty path."""
        cli = CLIAdapter(Mock())
        with pytest.raises(InvalidWatermarkError, match="cannot be empty"):
            cli._validate_image_path("")


# ============================================================================
# Integration Tests (Optional - require test PDF files)
# ============================================================================


@pytest.mark.skip(reason="Requires test PDF file - enable for integration testing")
def test_full_watermarking_integration(tmp_path):
    """Full end-to-end test with real adapters.

    To enable: create a test PDF and remove the skip decorator.
    """
    from pdfmarker.infrastructure.adapters import PyPDF2Repository, ReportLabRenderer

    # Create real adapters
    pdf_repo = PyPDF2Repository()
    renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repo, renderer)

    # Create watermark
    style = WatermarkStyle()
    watermark = Watermark(type=WatermarkType.TEXT, content="TEST", style=style)

    # Apply to test PDF (you'd need to create a test.pdf)
    # output = service.apply_watermark_to_pdf("test.pdf", watermark)
    # assert os.path.exists(output)
