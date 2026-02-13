# Commit Skill - PDFMarker

## Description

Hace git commit de los cambios realizados. Usa commits atómicos por capa con mensajes descriptivos.

## Trigger

Se ejecuta al FINAL de una tarea completa, después de que el ciclo TDD esté completo y lint pase.

## Commands

```bash
# Ver estado
git status

# Ver cambios
git diff --staged

# Commit con mensaje
git commit -m "<mensaje>"
```

## Mensaje de Commit

Formato por capa:

```
<capa>: <descripción corta>

- <detalle 1>
- <detalle 2>
```

### Capas válidas

- `domain`
- `application`
- `infrastructure`
- `testing`
- `refactor` (para refactors que no son de una capa específica)

## Usage

```
skill("commit", { layer: "domain", message: "add ImagePosition enum" })
```

O manualmente:

```
/commit domain add ImagePosition enum
```

## Workflow

```
1. Verificar que lint haya pasado
2. git status → ver archivos cambiados
3. git diff --staged → revisar cambios
4. Determinar qué capa se modificó principalmente
5. Escribir mensaje de commit
6. git add -A
7. git commit -m "..."
8. Reportar commit hash
```

## Constraints

- UN commit por tarea completa, NO por cada paso
- Mensajes descriptivos y significativos
- Incluir contexto si es necesario
- NO hacer commit de archivos con secrets

## Example

```
domain: add ImagePosition enum for watermark placement

- Add ImagePosition enum with CENTER, TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT
- Add validation in WatermarkStyle __post_init__
- Add tests for position validation
```

## On Error

Si el commit falla:

1. Verificar原因 (hooks, conflicts, etc)
2. Corregir el problema
3. Reintentar
