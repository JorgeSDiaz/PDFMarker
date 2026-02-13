# PDFMarker

CLI para aplicar marcas de agua a PDFs (texto o imagen).

## Install

```bash
pip install -r requirements.txt
```

## CLI

```bash
python main.py
```

Ejemplo interactivo:

```
Enter base PDF path: sample.pdf
Watermark type (text/image): text
Enter watermark text: CONFIDENTIAL
✓ Watermark applied: sample_watermarked.pdf
```

Para marcas de agua de imagen:

```
Watermark type (text/image): image
Enter image path: logo.png
Image Scale Options:
  1. Small    (20%)
  2. Medium   (40%)
  3. Large    (60%)
  4. Original [default]
  5. Custom
Select scale (1-5) [4]: 2
```

## Library

```python
from pdfmarker.domain.models import Watermark, WatermarkStyle, WatermarkType
from pdfmarker.infrastructure.adapters import PDFRepository, ReportLabRenderer
from pdfmarker.application.services import WatermarkingServiceImpl

# Setup
service = WatermarkingServiceImpl(PDFRepository(), ReportLabRenderer())

# Text watermark
style = WatermarkStyle(opacity=0.5, rotation=30, size=36, font="Helvetica")
watermark = Watermark(type=WatermarkType.TEXT, content="DRAFT", style=style)
service.apply_watermark_to_pdf("input.pdf", watermark)
```

## Options

| Parameter | Type  | Default   |
| --------- | ----- | --------- |
| opacity   | float | 0.3       |
| rotation  | int   | 45        |
| font      | str   | Helvetica |
| size      | int   | 28        |

Image scale presets: Small (20%), Medium (40%), Large (60%), Original, Custom (5-100%)

## Requirements

Python 3.8+ • pypdf • ReportLab 4.0+

## Architecture

Hexagonal (Ports & Adapters): domain/application/infrastructure layers
