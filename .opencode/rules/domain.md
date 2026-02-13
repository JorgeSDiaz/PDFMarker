# Domain Layer Rules

The domain layer contains pure business logic with **zero external dependencies**.

## Files

- `pdfmarker/domain/models.py` - Entities and Value Objects
- `pdfmarker/domain/exceptions.py` - Domain exceptions

## Rules

### Zero Dependencies

- Only use Python stdlib (dataclasses, enum, typing, pathlib)
- NO imports from PyPDF2, ReportLab, FastAPI, or any external library

### Dataclasses

Use `@dataclass(frozen=True)` for value objects (immutable):

```python
@dataclass(frozen=True)
class WatermarkStyle:
    opacity: float = 0.3
    rotation: int = 45

    def __post_init__(self) -> None:
        if not 0 <= self.opacity <= 1:
            raise InvalidWatermarkError(f"Opacity must be 0-1, got {self.opacity}")
```

Use `@dataclass` (mutable) for entities:

```python
@dataclass
class Watermark:
    type: WatermarkType
    content: str
    style: WatermarkStyle
```

### Validation

- All validation in `__post_init__` methods
- Raise domain-specific exceptions with descriptive messages
- Validate ranges, types, and business rules

### Enums

Use Python's `enum` module for type-safe constants:

```python
class WatermarkType(Enum):
    TEXT = "text"
    IMAGE = "image"

class ScalePreset(Enum):
    ORIGINAL = "original"
    FIT_PAGE = "fit_page"
    FIT_WIDTH = "fit_width"
    CUSTOM = "custom"
```

### Exceptions

Define domain exceptions in `exceptions.py`:

```python
class InvalidWatermarkError(ValueError):
    pass

class InvalidPDFError(ValueError):
    pass
```
