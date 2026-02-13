# Lint Skill - PDFMarker

## Description

Ejecuta verificación de código (lint) y tests para el código modificado. Usa ruff para linting y pytest para tests.

## Trigger

Se ejecuta manualmente o automáticamente después de refactorizar código.

## Commands

```bash
# Run ruff on modified files
ruff check .

# Run ruff with auto-fix
ruff check . --fix

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_domain.py -v
```

## Usage

```
skill("lint")
```

O manualmente:

```
/lint
```

## What it checks

1. **Ruff**: Code quality, imports, formatting
2. **Pytest**: Unit tests and integration tests
3. **Type hints**: Verifica que type hints estén presentes

## Exit Codes

- 0: Todo OK
- 1: Errores encontrados

## On Error

Si el lint falla:

1. Leer los errores
2. Corregir los problemas encontrados
3. Volver a ejecutar skill(lint)
4. Si persiste, evaluar si es un false positive

## Constraints

- NO modificar código automáticamente (solo --fix para issues simples)
- Si hay muchos errores, priorizar los críticos
- Verificar que los tests pasen después de lint
