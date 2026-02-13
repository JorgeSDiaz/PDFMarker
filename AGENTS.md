# AGENTS.md - PDFMarker Developer Guide

Quick reference for AI agents. For detailed rules by layer, see @.opencode/rules/_.md.
For agent orchestration, see @.opencode/agents/_.md. For skills, see @.opencode/skills/\*/SKILL.md.

## Build Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_watermarking.py::TestWatermarkStyle -v

# Run single test
pytest tests/test_watermarking.py::TestWatermarkStyle::test_default_values -v

# With coverage
pytest tests/ --cov=pdfmarker --cov-report=html

# Run CLI
python main.py
```

## Project Structure

```
pdfmarker/
├── domain/           # Business logic (zero deps) → @.opencode/rules/domain.md
├── application/      # Ports + Services → @.opencode/rules/application.md
└── infrastructure/   # Adapters → @.opencode/rules/infrastructure.md

tests/
└── test_watermarking.py  → @.opencode/rules/testing.md
```

## Architecture Summary

Hexagonal Architecture with dependency flow:

```
infrastructure → application → domain
```

- **Domain**: Pure Python, zero external deps
- **Application**: Imports only from domain
- **Infrastructure**: Implements ports, contains all external imports

## Code Style

- Python 3.8+, 4 spaces, PEP 8
- Type hints required
- Dataclasses: `frozen=True` for value objects
- Interfaces: `typing.Protocol` (not ABC)
- Private attributes: `_prefix`

## Key Files

| File                                   | Purpose                                |
| -------------------------------------- | -------------------------------------- |
| `pdfmarker/domain/models.py`           | Watermark, PDFDocument, WatermarkStyle |
| `pdfmarker/application/ports.py`       | Protocol definitions                   |
| `pdfmarker/application/services.py`    | WatermarkingServiceImpl                |
| `pdfmarker/infrastructure/adapters.py` | PDFRepository, ReportLabRenderer       |
| `pdfmarker/infrastructure/cli.py`      | CLIAdapter + composition root          |

## Testing

Tests organized by layer:

- Domain: @.opencode/rules/testing.md → tests/test_domain.py
- Application: tests/test_application.py
- Infrastructure: tests/test_infrastructure.py
- Integration: tests/test_watermarking.py

## Agent System

See @.opencode/agents/orchestrator.agent.md for orchestration.

| Agent          | Layer          | Files                    |
| -------------- | -------------- | ------------------------ |
| orchestrator   | Coordination   | Coordinates all agents   |
| domain         | domain         | models.py, exceptions.py |
| application    | application    | ports.py, services.py    |
| infrastructure | infrastructure | adapters.py, cli.py      |
| testing        | testing        | tests/\*.py              |

## Skills

| Skill  | Purpose             |
| ------ | ------------------- |
| lint   | Run ruff + pytest   |
| commit | Git commit by layer |
