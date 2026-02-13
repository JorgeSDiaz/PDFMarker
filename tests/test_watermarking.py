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
    ScalePreset,
    ImageScaleConfig,
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
        with pytest.raises(
            InvalidWatermarkError, match="Opacity must be between 0 and 1"
        ):
            WatermarkStyle(opacity=1.5)

    def test_opacity_validation_negative(self):
        """Test opacity validation rejects negative values."""
        with pytest.raises(
            InvalidWatermarkError, match="Opacity must be between 0 and 1"
        ):
            WatermarkStyle(opacity=-0.1)

    def test_rotation_validation_too_high(self):
        """Test rotation validation rejects values > 360."""
        with pytest.raises(
            InvalidWatermarkError, match="Rotation must be between 0 and 360"
        ):
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
        watermark = Watermark(
            type=WatermarkType.TEXT, content="CONFIDENTIAL", style=style
        )

        assert watermark.type == WatermarkType.TEXT
        assert watermark.content == "CONFIDENTIAL"
        assert watermark.style.opacity == 0.3

    def test_empty_content_validation(self):
        """Test that empty content is rejected."""
        style = WatermarkStyle()
        with pytest.raises(InvalidWatermarkError, match="content cannot be empty"):
            Watermark(type=WatermarkType.TEXT, content="", style=style)


class TestImageScaleConfig:
    """Test ImageScaleConfig value object validation."""

    def test_default_preset_is_original(self):
        """Test default preset is ORIGINAL."""
        config = ImageScaleConfig()
        assert config.preset == ScalePreset.ORIGINAL
        assert config.custom_percentage is None

    def test_small_preset_returns_20_percent(self):
        """Test SMALL preset returns 20% percentage."""
        config = ImageScaleConfig(preset=ScalePreset.SMALL)
        assert config.get_percentage() == 20.0

    def test_medium_preset_returns_40_percent(self):
        """Test MEDIUM preset returns 40% percentage."""
        config = ImageScaleConfig(preset=ScalePreset.MEDIUM)
        assert config.get_percentage() == 40.0

    def test_large_preset_returns_60_percent(self):
        """Test LARGE preset returns 60% percentage."""
        config = ImageScaleConfig(preset=ScalePreset.LARGE)
        assert config.get_percentage() == 60.0

    def test_original_preset_returns_none(self):
        """Test ORIGINAL preset returns None from get_percentage()."""
        config = ImageScaleConfig(preset=ScalePreset.ORIGINAL)
        assert config.get_percentage() is None

    def test_custom_preset_with_valid_percentage(self):
        """Test CUSTOM preset with valid percentage works."""
        config = ImageScaleConfig(preset=ScalePreset.CUSTOM, custom_percentage=75.0)
        assert config.get_percentage() == 75.0

    def test_custom_preset_without_percentage_raises_error(self):
        """Test CUSTOM preset without percentage raises error."""
        with pytest.raises(InvalidWatermarkError, match="custom_percentage required"):
            ImageScaleConfig(preset=ScalePreset.CUSTOM)

    def test_custom_percentage_below_minimum_raises_error(self):
        """Test custom percentage < 5 raises error."""
        with pytest.raises(
            InvalidWatermarkError, match="custom_percentage must be 5-100"
        ):
            ImageScaleConfig(preset=ScalePreset.CUSTOM, custom_percentage=3.0)

    def test_custom_percentage_above_maximum_raises_error(self):
        """Test custom percentage > 100 raises error."""
        with pytest.raises(
            InvalidWatermarkError, match="custom_percentage must be 5-100"
        ):
            ImageScaleConfig(preset=ScalePreset.CUSTOM, custom_percentage=150.0)

    def test_custom_percentage_with_non_custom_preset_raises_error(self):
        """Test custom percentage with non-CUSTOM preset raises error."""
        with pytest.raises(
            InvalidWatermarkError, match="only valid with CUSTOM preset"
        ):
            ImageScaleConfig(preset=ScalePreset.SMALL, custom_percentage=50.0)

    def test_immutability(self):
        """Test that ImageScaleConfig is immutable (frozen)."""
        config = ImageScaleConfig()
        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            config.preset = ScalePreset.LARGE


class TestWatermarkWithImageScale:
    """Test Watermark entity with image_scale field."""

    def test_image_watermark_accepts_image_scale(self):
        """Test IMAGE watermark accepts image_scale."""
        style = WatermarkStyle()
        scale = ImageScaleConfig(preset=ScalePreset.LARGE)
        watermark = Watermark(
            type=WatermarkType.IMAGE, content="logo.png", style=style, image_scale=scale
        )

        assert watermark.image_scale.preset == ScalePreset.LARGE

    def test_text_watermark_rejects_image_scale(self):
        """Test TEXT watermark rejects image_scale."""
        style = WatermarkStyle()
        scale = ImageScaleConfig(preset=ScalePreset.LARGE)

        with pytest.raises(
            InvalidWatermarkError, match="only valid for IMAGE watermarks"
        ):
            Watermark(
                type=WatermarkType.TEXT,
                content="CONFIDENTIAL",
                style=style,
                image_scale=scale,
            )

    def test_image_watermark_without_image_scale_is_valid(self):
        """Test IMAGE watermark works without image_scale (backward compatible)."""
        style = WatermarkStyle()
        watermark = Watermark(
            type=WatermarkType.IMAGE, content="logo.png", style=style, image_scale=None
        )

        assert watermark.image_scale is None


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
        assert (
            service._generate_output_path("document.pdf") == "document_watermarked.pdf"
        )
        assert (
            service._generate_output_path("/path/to/doc.pdf")
            == "/path/to/doc_watermarked.pdf"
        )

    def test_apply_watermark_with_image_scale(self):
        """Test that image_scale flows through service correctly."""
        # Arrange
        mock_pdf_repo = Mock(spec=PDFRepository)
        mock_renderer = Mock(spec=WatermarkRenderer)

        mock_pdf_repo.read.return_value = PDFDocument(
            width=612.0, height=792.0, pages=1
        )
        mock_renderer.render.return_value = "/tmp/watermark.pdf"

        service = WatermarkingServiceImpl(mock_pdf_repo, mock_renderer)

        # Create watermark with LARGE preset
        style = WatermarkStyle()
        scale = ImageScaleConfig(preset=ScalePreset.LARGE)
        watermark = Watermark(
            type=WatermarkType.IMAGE, content="logo.png", style=style, image_scale=scale
        )

        # Act
        service.apply_watermark_to_pdf("input.pdf", watermark)

        # Assert - verify renderer receives watermark with scale config
        mock_renderer.render.assert_called_once()
        call_args = mock_renderer.render.call_args
        rendered_watermark = call_args[0][0]
        assert rendered_watermark.image_scale.preset == ScalePreset.LARGE


# ============================================================================
# Infrastructure Layer Tests - ReportLab Renderer Scaling
# ============================================================================


class TestReportLabRendererScaling:
    """Test ReportLabRenderer image scaling algorithm."""

    def _create_test_image(self, path, width, height):
        """Helper to create a test image with specific dimensions."""
        from PIL import Image

        img = Image.new("RGB", (width, height), color="red")
        img.save(path)

    def test_backward_compatibility_none_scale_config(self, tmp_path):
        """Test backward compatibility: None scale_config returns (−100, −100, 200, 200)."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create test image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 1024, 1024)

        renderer = ReportLabRenderer()
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path),
            (612.0, 792.0),  # Letter size PDF
            None,  # No scale config = backward compatible
        )

        assert x == -100
        assert y == -100
        assert width == 200
        assert height == 200

    def test_original_preset_with_square_image(self, tmp_path):
        """Test ORIGINAL preset with square image uses original dimensions."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create 1024x1024 test image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 1024, 1024)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.ORIGINAL)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path),
            (612.0, 792.0),  # Letter size PDF
            scale_config,
        )

        # 1024px image limited to 95% of 612pt = 581.4pt
        assert width == pytest.approx(581.4, rel=1e-2)
        assert height == pytest.approx(581.4, rel=1e-2)  # Square, so same
        assert x == pytest.approx(-581.4 / 2, rel=1e-2)
        assert y == pytest.approx(-581.4 / 2, rel=1e-2)

    def test_original_preset_with_large_image_gets_limited(self, tmp_path):
        """Test ORIGINAL preset with large image gets limited to 95% of PDF."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create huge image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 2000, 2000)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.ORIGINAL)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # Should be limited to 95% of PDF width
        assert width == pytest.approx(612.0 * 0.95, rel=1e-2)
        assert height == pytest.approx(612.0 * 0.95, rel=1e-2)  # Square

    def test_medium_preset_scales_correctly(self, tmp_path):
        """Test MEDIUM preset (40%) scales correctly relative to PDF width."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create square image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 1024, 1024)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.MEDIUM)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # 40% of 612pt = 244.8pt
        expected_width = 612.0 * 0.4
        assert width == pytest.approx(expected_width, rel=1e-2)
        assert height == pytest.approx(expected_width, rel=1e-2)  # Square

    def test_aspect_ratio_preserved_for_wide_image(self, tmp_path):
        """Test aspect ratio preserved for non-square images (2:1)."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create 2:1 aspect ratio image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 2000, 1000)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.MEDIUM)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # 40% of 612pt = 244.8pt width
        expected_width = 612.0 * 0.4
        expected_height = expected_width / 2  # 2:1 aspect ratio

        assert width == pytest.approx(expected_width, rel=1e-2)
        assert height == pytest.approx(expected_height, rel=1e-2)

    def test_aspect_ratio_preserved_for_tall_image(self, tmp_path):
        """Test aspect ratio preserved for tall images (1:2)."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create 1:2 aspect ratio image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 1000, 2000)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.LARGE)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # 60% of 612pt = 367.2pt width
        expected_width = 612.0 * 0.6
        expected_height = expected_width * 2  # 1:2 aspect ratio

        assert width == pytest.approx(expected_width, rel=1e-2)
        assert height == pytest.approx(expected_height, rel=1e-2)

    def test_height_limit_constrains_dimensions(self, tmp_path):
        """Test that height limit (95%) constrains dimensions independently."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create very tall image (1:4 aspect ratio)
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 500, 2000)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.LARGE)
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # Height should be limited to 95% of PDF height (752.4pt)
        # Then width adjusted to maintain aspect ratio
        expected_height = 792.0 * 0.95
        expected_width = expected_height / 4  # 1:4 aspect ratio

        assert height == pytest.approx(expected_height, rel=1e-2)
        assert width == pytest.approx(expected_width, rel=1e-2)

    def test_invalid_image_path_raises_error(self):
        """Test that invalid image path raises InvalidWatermarkError."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(preset=ScalePreset.MEDIUM)

        with pytest.raises(InvalidWatermarkError, match="Image file not found"):
            renderer._calculate_image_dimensions(
                "/nonexistent/image.png", (612.0, 792.0), scale_config
            )

    def test_custom_preset_scales_correctly(self, tmp_path):
        """Test CUSTOM preset with 75% scales correctly."""
        from pdfmarker.infrastructure.adapters import ReportLabRenderer

        # Create square image
        image_path = tmp_path / "test.png"
        self._create_test_image(image_path, 1024, 1024)

        renderer = ReportLabRenderer()
        scale_config = ImageScaleConfig(
            preset=ScalePreset.CUSTOM, custom_percentage=75.0
        )
        x, y, width, height = renderer._calculate_image_dimensions(
            str(image_path), (612.0, 792.0), scale_config
        )

        # 75% of 612pt = 459pt
        expected_width = 612.0 * 0.75
        assert width == pytest.approx(expected_width, rel=1e-2)
        assert height == pytest.approx(expected_width, rel=1e-2)  # Square


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
    from pdfmarker.infrastructure.adapters import PDFRepository, ReportLabRenderer

    # Create real adapters
    pdf_repo = PDFRepository()
    renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repo, renderer)

    # Create watermark
    style = WatermarkStyle()
    watermark = Watermark(type=WatermarkType.TEXT, content="TEST", style=style)

    # Apply to test PDF (you'd need to create a test.pdf)
    # output = service.apply_watermark_to_pdf("test.pdf", watermark)
    # assert os.path.exists(output)
