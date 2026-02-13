# Architecture Rules

PDFMarker uses **Hexagonal Architecture** (Ports & Adapters pattern).

## Dependency Flow

```
infrastructure/ → application/ → domain/
   (adapters)      (ports)       (models)
```

- **Domain**: Zero external dependencies (stdlib only)
- **Application**: Imports only from domain
- **Infrastructure**: Implements ports, contains all external imports

## Ports & Adapters

### Inbound Ports (What the app offers)

- `WatermarkingService` - Use case interface
- Called by: CLIAdapter, future APIAdapter

### Outbound Ports (What the app needs)

- `PDFRepository` - PDF operations interface
- `WatermarkRenderer` - Watermark rendering interface

## Composition Root

The only place that wires dependencies is `infrastructure/cli.py:main()`:

```python
def main() -> None:
    pdf_repo = PyPDF2Repository()
    renderer = ReportLabRenderer()
    service = WatermarkingServiceImpl(pdf_repo, renderer)
    cli = CLIAdapter(service)
    cli.run()
```

## Key Principles

1. Domain has ZERO external imports
2. Use `typing.Protocol` for interfaces (not ABC)
3. Dependency injection throughout
4. All external libs in infrastructure layer only

For detailed layer rules, see:

- @.opencode/rules/domain.md
- @.opencode/rules/application.md
- @.opencode/rules/infrastructure.md
