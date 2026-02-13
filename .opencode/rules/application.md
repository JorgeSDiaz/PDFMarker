# Application Layer Rules

The application layer contains use cases and hexagon boundaries (ports).

## Files

- `pdfmarker/application/ports.py` - Protocol definitions
- `pdfmarker/application/services.py` - Service implementations

## Rules

### Dependencies

- Import ONLY from domain layer
- NO imports from infrastructure layer
- Use dependency injection for adapters

### Protocols (Interfaces)

Use `typing.Protocol` for duck typing (NOT ABC):

```python
from typing import Protocol

class PDFRepository(Protocol):
    def read(self, path: str) -> PDFDocument: ...
    def merge_watermark(self, pdf_path: str, watermark_path: str, output_path: str) -> None: ...

class WatermarkRenderer(Protocol):
    def render(self, watermark: Watermark, dimensions: tuple[float, float]) -> str: ...
```

### Services

Service implementations use dependency injection:

```python
class WatermarkingServiceImpl:
    def __init__(self, pdf_repo: PDFRepository, renderer: WatermarkRenderer) -> None:
        self._pdf_repo = pdf_repo    # Port, not concrete class
        self._renderer = renderer     # Port, not concrete class

    def apply_watermark_to_pdf(self, pdf_path: str, watermark: Watermark) -> str:
        pdf_doc = self._pdf_repo.read(pdf_path)
        watermark_path = self._renderer.render(watermark, (pdf_doc.width, pdf_doc.height))
        output_path = self._generate_output_path(pdf_path)
        self._pdf_repo.merge_watermark(pdf_path, watermark_path, output_path)
        return output_path
```

### Private Attributes

- Prefix private attributes with `_` (e.g., `self._pdf_repo`)
- Keep references to ports, not concrete implementations
