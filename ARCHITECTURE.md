# PDFMarker - Hexagonal Architecture Documentation

## Overview

PDFMarker has been refactored from a monolithic 73-line script into a clean **Hexagonal Architecture** (Ports & Adapters pattern) with 10 well-organized files.

## Architecture Comparison

### Before (Monolithic)
```
main.py (73 lines)
├── generate_watermark()        # ReportLab directly
├── generate_watermarked_pdf()  # PyPDF2 directly
└── main()                      # Mixed CLI + business logic
```

**Problems:**
- ❌ Business logic mixed with CLI (`input()` calls)
- ❌ Hard to test (no dependency injection)
- ❌ Hard to extend (adding REST API requires full rewrite)
- ❌ Direct dependencies on PyPDF2/ReportLab everywhere

### After (Hexagonal Architecture)

```
pdfmarker/
├── domain/                     # INNER HEXAGON (Business Logic)
│   ├── models.py              # 80 lines - Entities + Value Objects
│   └── exceptions.py          # 20 lines - Domain exceptions
│
├── application/                # APPLICATION LAYER (Use Cases + Ports)
│   ├── ports.py              # 60 lines - All ports (Protocol)
│   └── services.py           # 100 lines - Use case orchestration
│
└── infrastructure/             # OUTER HEXAGON (Adapters)
    ├── adapters.py           # 150 lines - PyPDF2 + ReportLab
    └── cli.py                # 80 lines - CLI + composition root

main.py                         # 10 lines - Entry point
tests/test_watermarking.py      # 170 lines - Comprehensive tests
```

**Benefits:**
- ✅ Pure business logic (domain has 0 external dependencies)
- ✅ Testable with mocks (14 passing unit tests)
- ✅ REST-ready (add new adapter, no domain changes)
- ✅ Clear boundaries via Python Protocols
- ✅ ~70 lines average per file (maintainable)

## Hexagonal Architecture Principles

### 1. Dependency Rule

```
Infrastructure → Application → Domain
(adapters)       (ports/services)  (models)
```

- **Domain** imports nothing (pure business logic)
- **Application** imports only domain (uses ports for infrastructure)
- **Infrastructure** imports application + domain (implements ports)

### 2. Ports & Adapters

**Inbound Ports** (what the app offers):
- `WatermarkingService` - Use case interface
- Implemented by: `WatermarkingServiceImpl`
- Called by: `CLIAdapter`, future `APIAdapter`

**Outbound Ports** (what the app needs):
- `PDFRepository` - PDF operations interface
- `WatermarkRenderer` - Watermark rendering interface
- Implemented by: `PyPDF2Repository`, `ReportLabRenderer`

### 3. Dependency Injection

**Composition Root** in `infrastructure/cli.py:main()`:

```python
def main():
    # Create adapters (infrastructure)
    pdf_repo = PyPDF2Repository()
    renderer = ReportLabRenderer()

    # Inject into service (application)
    service = WatermarkingServiceImpl(pdf_repo, renderer)

    # Inject into CLI (inbound adapter)
    cli = CLIAdapter(service)

    # Run
    cli.run()
```

This is the **ONLY** place that knows about concrete implementations.

## Layer Responsibilities

### Domain Layer (`domain/`)

**Purpose:** Pure business logic with zero external dependencies

**Files:**
- `models.py` - Entities (`Watermark`, `PDFDocument`) and Value Objects (`WatermarkStyle`)
- `exceptions.py` - Domain-specific exceptions

**Rules:**
- ✅ Can use Python stdlib (dataclasses, enum, typing)
- ❌ Cannot import PyPDF2, ReportLab, FastAPI
- ✅ Validation in `__post_init__`
- ✅ Frozen dataclasses for immutability (value objects)

**Example:**
```python
@dataclass(frozen=True)
class WatermarkStyle:
    opacity: float = 0.3
    rotation: int = 45

    def __post_init__(self):
        if not 0 <= self.opacity <= 1:
            raise InvalidWatermarkError("Opacity must be 0-1")
```

### Application Layer (`application/`)

**Purpose:** Use cases and hexagon boundaries (ports)

**Files:**
- `ports.py` - Protocol definitions (duck typing interfaces)
- `services.py` - Use case implementations

**Rules:**
- ✅ Can import from domain
- ❌ Cannot import from infrastructure
- ✅ Depends on ports (abstractions), not implementations
- ✅ Orchestrates domain logic

**Example:**
```python
class WatermarkingServiceImpl:
    def __init__(self, pdf_repo: PDFRepository, renderer: WatermarkRenderer):
        self._pdf_repo = pdf_repo    # Port, not concrete class
        self._renderer = renderer     # Port, not concrete class

    def apply_watermark_to_pdf(self, pdf_path: str, watermark: Watermark) -> str:
        # Orchestrate: read → render → merge
        pdf_doc = self._pdf_repo.read(pdf_path)
        watermark_path = self._renderer.render(watermark, (pdf_doc.width, pdf_doc.height))
        # ...
```

### Infrastructure Layer (`infrastructure/`)

**Purpose:** Concrete implementations (adapters to external systems)

**Files:**
- `adapters.py` - PyPDF2 and ReportLab adapters
- `cli.py` - CLI adapter + composition root

**Rules:**
- ✅ Can import from application and domain
- ✅ Implements ports (outbound adapters)
- ✅ Contains all external library imports
- ✅ Composition root wires dependencies

**Example:**
```python
class PyPDF2Repository:
    """Implements PDFRepository port"""

    def read(self, path: str) -> PDFDocument:
        reader = PdfReader(path)  # PyPDF2 import only here
        # ...
        return PDFDocument(width, height, pages)
```

## Testing Strategy

### Domain Tests
```python
def test_watermark_style_validation():
    with pytest.raises(InvalidWatermarkError):
        WatermarkStyle(opacity=1.5)  # Invalid opacity
```

- Test validation logic
- No mocks needed (pure functions)
- Fast and reliable

### Application Tests
```python
def test_apply_watermark_service():
    mock_repo = Mock(spec=PDFRepository)
    mock_renderer = Mock(spec=WatermarkRenderer)
    service = WatermarkingServiceImpl(mock_repo, mock_renderer)
    # Test orchestration with mocks
```

- Test use case orchestration
- Mock ports (not implementations)
- Verify interactions

### Infrastructure Tests
- Test adapters with real libraries (optional)
- Integration tests (end-to-end)

## Extending the Application

### Adding REST API (Example: FastAPI)

**Step 1:** Create new inbound adapter

```python
# infrastructure/api.py
from fastapi import FastAPI, UploadFile
from pdfmarker.application.services import WatermarkingServiceImpl

app = FastAPI()

class APIAdapter:
    def __init__(self, service: WatermarkingServiceImpl):
        self._service = service

@app.post("/watermark")
async def watermark_endpoint(file: UploadFile, text: str):
    # Same service, different adapter
    pass
```

**Step 2:** Update composition root

```python
# infrastructure/api.py
def create_app():
    # Same DI pattern as CLI
    pdf_repo = PyPDF2Repository()
    renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repo, renderer)
    return APIAdapter(service)
```

**Key Point:** Zero changes to domain or application layers!

### Switching PDF Libraries

To replace PyPDF2 with `pypdf` or another library:

1. Create `NewPDFRepository` implementing `PDFRepository` port
2. Update composition root:
   ```python
   pdf_repo = NewPDFRepository()  # Only change this line
   ```
3. Domain and application unchanged

## Code Metrics

| Layer | Files | Lines | Dependencies |
|-------|-------|-------|--------------|
| Domain | 2 | ~100 | 0 (pure Python) |
| Application | 2 | ~160 | Domain only |
| Infrastructure | 2 | ~230 | Application + Domain + External libs |
| Tests | 1 | ~170 | All layers |
| **Total** | **7** | **~660** | **Clean separation** |

Average file size: ~70 lines (easy to navigate)

## Key Insights

### Why Hexagonal Architecture?

1. **Framework Independence** - Business logic doesn't know about FastAPI/Flask
2. **Testability** - Pure domain, mockable ports
3. **Changeability** - Swap libraries without rewriting logic
4. **Clarity** - Clear boundaries between layers

### Why Python Protocols?

```python
from typing import Protocol

class PDFRepository(Protocol):
    def read(self, path: str) -> PDFDocument: ...
```

- ✅ Duck typing (Pythonic)
- ✅ No inheritance required
- ✅ Type checking with mypy
- ❌ Not Java-style ABC over-engineering

### Composition Root Pattern

The `main()` function in `infrastructure/cli.py` is the **only place** that knows about:
- Concrete adapter implementations
- Dependency wiring
- System configuration

This enables:
- Easy testing (inject mocks)
- Easy extension (swap implementations)
- Clear architecture (explicit dependencies)

## References

- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Ports & Adapters Pattern](https://softwarecampament.wordpress.com/portsadapters/)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
