# PDFMarker

A Python CLI application for applying watermarks to PDF files, built with **Hexagonal Architecture** (Ports & Adapters).

## Features

- ✅ Apply text watermarks to PDF files
- ✅ Configurable opacity, rotation, font size
- ✅ Support for multi-page PDFs
- ✅ Clean hexagonal architecture (domain/application/infrastructure)
- ✅ Framework-agnostic design (REST API ready)
- ✅ Fully tested with unit tests

## Architecture

This project uses **Hexagonal Architecture** (also called Ports & Adapters) to separate business logic from infrastructure concerns.

```
pdfmarker/
├── domain/                     # Inner hexagon (business logic)
│   ├── models.py              # Entities + Value Objects
│   └── exceptions.py          # Domain exceptions
│
├── application/                # Application layer (use cases + ports)
│   ├── ports.py              # All ports (inbound + outbound)
│   └── services.py           # Application services (use cases)
│
└── infrastructure/             # Outer hexagon (adapters)
    ├── adapters.py           # PDF + Rendering adapters
    └── cli.py                # CLI adapter + DI setup
```

### Layers

**Domain Layer** (`domain/`)
- Pure business logic with **zero external dependencies**
- Entities: `Watermark`, `PDFDocument`
- Value Objects: `WatermarkStyle`
- No imports of PyPDF2, ReportLab, FastAPI

**Application Layer** (`application/`)
- Use cases and ports (hexagon boundaries)
- `WatermarkingService` - inbound port (what the app offers)
- `PDFRepository`, `WatermarkRenderer` - outbound ports (what the app needs)
- Uses Python's `Protocol` for duck typing (not ABC)

**Infrastructure Layer** (`infrastructure/`)
- Concrete implementations of ports
- `PyPDF2Repository` - PDF operations with PyPDF2
- `ReportLabRenderer` - Watermark rendering with ReportLab
- `CLIAdapter` - Command-line interface
- **Composition root** in `main()` - dependency injection setup

### Benefits

✅ **Framework-agnostic** - Business logic independent of FastAPI/Flask/Django
✅ **Testable** - Domain is pure, services use mocked ports
✅ **REST-ready** - Add REST API = new adapter, 0 changes to domain/application
✅ **Maintainable** - Clear separation of concerns (10 files, ~70 lines avg)
✅ **Pythonic** - Protocols, dataclasses, type hints

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PDFMarker.git
cd PDFMarker

# Install dependencies
pip install -r requirements.txt
```

## Usage

### CLI

```bash
python main.py
```

**Example:**
```
Enter base PDF path: sample.pdf
Enter watermark text: CONFIDENTIAL
✓ Watermark applied: sample_watermarked.pdf
```

### As a Library

```python
from pdfmarker.domain.models import Watermark, WatermarkStyle, WatermarkType
from pdfmarker.infrastructure.adapters import PyPDF2Repository, ReportLabRenderer
from pdfmarker.application.services import WatermarkingServiceImpl

# Create adapters
pdf_repo = PyPDF2Repository()
renderer = ReportLabRenderer()

# Create service
service = WatermarkingServiceImpl(pdf_repo, renderer)

# Create watermark
style = WatermarkStyle(opacity=0.5, rotation=30)
watermark = Watermark(type=WatermarkType.TEXT, content="DRAFT", style=style)

# Apply watermark
output = service.apply_watermark_to_pdf("input.pdf", watermark)
print(f"Created: {output}")
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=pdfmarker --cov-report=html
```

### Project Structure

```
PDFMarker/
├── main.py                     # Entry point
├── pdfmarker/                  # Main package
│   ├── domain/                # Business logic (0 dependencies)
│   │   ├── models.py
│   │   └── exceptions.py
│   ├── application/           # Use cases + ports
│   │   ├── ports.py
│   │   └── services.py
│   └── infrastructure/        # Adapters
│       ├── adapters.py
│       └── cli.py
├── tests/                      # Unit tests
│   └── test_watermarking.py
├── requirements.txt
└── README.md
```

## Extending the Application

### Adding a REST API

The hexagonal architecture makes it easy to add new interfaces without modifying existing code.

**Example: FastAPI adapter** (create `infrastructure/api.py`)

```python
from fastapi import FastAPI, UploadFile
from pdfmarker.domain.models import Watermark, WatermarkStyle, WatermarkType
from pdfmarker.infrastructure.adapters import PyPDF2Repository, ReportLabRenderer
from pdfmarker.application.services import WatermarkingServiceImpl

app = FastAPI()

# Composition root (same pattern as CLI)
pdf_repo = PyPDF2Repository()
renderer = ReportLabRenderer()
service = WatermarkingServiceImpl(pdf_repo, renderer)

@app.post("/watermark")
async def apply_watermark(file: UploadFile, text: str, opacity: float = 0.3):
    # Save uploaded file
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Create watermark (same domain objects as CLI)
    style = WatermarkStyle(opacity=opacity)
    watermark = Watermark(type=WatermarkType.TEXT, content=text, style=style)

    # Use same service as CLI
    output = service.apply_watermark_to_pdf(temp_path, watermark)
    return {"output": output}
```

**Key point:** CLI and REST API share the same business logic (domain + application layers). Only the adapter changes.

### Switching PDF Libraries

To use a different PDF library, just create a new adapter:

1. Create new adapter implementing `PDFRepository` port
2. Update composition root in `infrastructure/cli.py`
3. **No changes needed** to domain or application layers

## Requirements

- Python 3.8+
- PyPDF2 3.0+
- ReportLab 4.0+

## License

MIT License

## Architecture Diagrams

### Hexagonal Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                     Inbound Adapters                     │
│              (CLI, REST API, GUI - future)               │
│                                                           │
│  ┌─────────────┐                    ┌─────────────┐     │
│  │ CLIAdapter  │────────────────────│ APIAdapter  │     │
│  └──────┬──────┘                    └──────┬──────┘     │
└─────────┼──────────────────────────────────┼────────────┘
          │                                   │
          │  WatermarkingService (port)       │
          └───────────────┬───────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                         ▼                                  │
│             ┌────────────────────────┐                     │
│             │ WatermarkingServiceImpl│                     │
│             └─────────┬───────┬──────┘                     │
│   Application Layer   │       │                            │
│                       │       │                            │
│      ┌────────────────┘       └─────────────┐             │
│      │ PDFRepository (port)   WatermarkRenderer (port)    │
└──────┼──────────────────────────────────────┼─────────────┘
       │                                       │
┌──────┼───────────────────────────────────────┼─────────────┐
│      ▼                                       ▼             │
│  ┌──────────────────┐           ┌─────────────────────┐   │
│  │ PyPDF2Repository │           │ ReportLabRenderer   │   │
│  └──────────────────┘           └─────────────────────┘   │
│                                                            │
│                    Outbound Adapters                       │
│              (PyPDF2, ReportLab, etc.)                     │
└────────────────────────────────────────────────────────────┘
```

### Dependency Rule

```
Infrastructure → Application → Domain
(adapters)       (ports/services)  (models)

✅ Infrastructure can import from Application and Domain
✅ Application can import from Domain
❌ Domain imports NOTHING (zero dependencies)
```

This ensures that business logic (domain) is isolated and can be tested independently.
