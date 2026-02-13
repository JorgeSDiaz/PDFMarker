# Infrastructure Layer Rules

The infrastructure layer contains concrete implementations (adapters to external systems).

## Files

- `pdfmarker/infrastructure/adapters.py` - PDF and Rendering adapters
- `pdfmarker/infrastructure/cli.py` - CLI adapter + composition root

## Rules

### External Dependencies

- ALL external library imports go here (pypdf, ReportLab, PIL)
- Domain and application layers must remain dependency-free

### Adapters

Implement ports defined in application layer:

```python
from pypdf import PdfReader, PdfWriter

class PDFRepository:
    """Implements PDFRepository port"""

    def read(self, path: str) -> PDFDocument:
        reader = PdfReader(path)
        page = reader.pages[0]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        return PDFDocument(width=width, height=height, page_count=len(reader.pages))

    def merge_watermark(self, pdf_path: str, watermark_path: str, output_path: str) -> None:
        # pypdf implementation
        pass
```

### Composition Root

The `main()` function in `infrastructure/cli.py` is the ONLY place that knows about:

- Concrete adapter implementations
- Dependency wiring
- System configuration

```python
def main() -> None:
    pdf_repo = PDFRepository()
    renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repo, renderer)
    cli = CLIAdapter(service)
    cli.run()
```

### CLI Adapter

- Handle user input/output
- Delegate to service layer
- No business logic in adapter
