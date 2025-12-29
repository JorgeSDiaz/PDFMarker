from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

TEXT_WATERMARK_TYPE = "text"
IMAGE_WATERMARK_TYPE = "image"

def generate_watermark(
        file_name: str, 
        width: float, height: float, 
        watermark_type: str = "text", 
        message: str = "", image_path: str = "",
    ) -> None:
    canvas = Canvas(file_name, pagesize=(width, height))

    canvas.setFont("Helvetica", 28)
    canvas.setFillColorRGB(0, 0, 0, alpha=0.3)
    canvas.saveState()

    canvas.translate(width / 2, height / 2)
    canvas.rotate(45)

    if watermark_type.lower() == IMAGE_WATERMARK_TYPE:
        canvas.drawImage(image_path, -100, -100, width=200, height=200, mask='auto')
    else:
        canvas.drawCentredString(0, 0, message.upper())
    
    canvas.restoreState()
    canvas.save()


def generate_watermarked_pdf(
        input_pdf_reader: PdfReader,
        output_pdf_path: str,
        watermark_pdf_path: str
    ) -> None:
    pdf_writer = PdfWriter()

    watermark_reader = PdfReader(watermark_pdf_path)
    watermark_page = watermark_reader.pages[0]

    for page in input_pdf_reader.pages:
        page.merge_page(watermark_page)
        pdf_writer.add_page(page)

    with open(output_pdf_path, "wb") as output_pdf:
        pdf_writer.write(output_pdf)


def main() -> None:
    base_pdf_path = str(input("Enter base PDF path: "))
    watermark_text = str(input("Enter watermark text: "))

    if not base_pdf_path.endswith(".pdf"):
        base_pdf_path += ".pdf"

    pdf_reader = PdfReader(base_pdf_path)
    width_pdf, heigh_pdf = pdf_reader.pages[0].mediabox.upper_right

    generate_watermark("watermarked.pdf", float(width_pdf), float(heigh_pdf), TEXT_WATERMARK_TYPE, watermark_text)
    generate_watermarked_pdf(pdf_reader, "watermarked_output.pdf", "watermarked.pdf")

if __name__ == "__main__":
    main() 