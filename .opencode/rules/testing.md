# Testing Rules

Tests are located in `tests/test_watermarking.py`.

## Test Organization

Organize tests by layer:

1. **Domain tests**: Test models and validation (no mocks needed)
2. **Application tests**: Test services with mocked ports
3. **Infrastructure tests**: Optional, tests adapters

## Test Classes

```python
class TestWatermarkStyle:
    """Domain tests for WatermarkStyle value object"""

    def test_default_values(self) -> None:
        style = WatermarkStyle()
        assert style.opacity == 0.3
        assert style.rotation == 45

    def test_opacity_validation_rejects_values_greater_than_one(self) -> None:
        with pytest.raises(InvalidWatermarkError, match="Opacity must be 0-1"):
            WatermarkStyle(opacity=1.5)


class TestWatermarkingService:
    """Application tests for WatermarkingService"""

    def test_apply_watermark_orchestrates_correctly(self) -> None:
        mock_repo = Mock(spec=PDFRepository)
        mock_renderer = Mock(spec=WatermarkRenderer)
        service = WatermarkingServiceImpl(mock_repo, mock_renderer)
        # Test orchestration
```

## Mocking

Use `Mock(spec=...)` to ensure mocks conform to protocols:

```python
from unittest.mock import Mock

mock_pdf_repo = Mock(spec=PDFRepository)
mock_renderer = Mock(spec=WatermarkRenderer)
```

## Assertions

Use descriptive assertions and match patterns:

```python
# Good - descriptive test name
def test_opacity_validation_rejects_values_greater_than_one(self) -> None:
    with pytest.raises(InvalidWatermarkError, match="Opacity must be 0-1"):
        WatermarkStyle(opacity=1.5)

# Good - clear assertions
assert watermark.type == WatermarkType.TEXT
assert watermark.content == "CONFIDENTIAL"
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Single test class
pytest tests/test_watermarking.py::TestWatermarkStyle -v

# Single test
pytest tests/test_watermarking.py::TestWatermarkStyle::test_default_values -v

# With coverage
pytest tests/ --cov=pdfmarker --cov-report=html
```
