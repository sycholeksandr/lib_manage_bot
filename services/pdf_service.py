from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def generate_qr_pdf(
    books: list,
    qr_generator_func,
    deep_link_builder,
) -> BytesIO:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cols = 2
    rows = 4
    items_per_page = cols * rows

    margin_x = 8 * mm
    margin_y = 8 * mm
    gutter_x = 4 * mm
    gutter_y = 4 * mm

    usable_width = page_width - 2 * margin_x - gutter_x
    usable_height = page_height - 2 * margin_y - 3 * gutter_y

    cell_width = usable_width / cols
    cell_height = usable_height / rows

    image_padding = 2 * mm

    for index, book in enumerate(books):
        position_on_page = index % items_per_page

        if index > 0 and position_on_page == 0:
            pdf.showPage()

        row = position_on_page // cols
        col = position_on_page % cols

        cell_x = margin_x + col * (cell_width + gutter_x)
        cell_y = page_height - margin_y - (row + 1) * cell_height - row * gutter_y

        deep_link = deep_link_builder(book.id)
        qr_buffer = qr_generator_func(data=deep_link, book_id=book.id)

        image = ImageReader(qr_buffer)

        max_image_width = cell_width - 2 * image_padding
        max_image_height = cell_height - 2 * image_padding

        img_width, img_height = image.getSize()
        scale = min(max_image_width / img_width, max_image_height / img_height)

        draw_width = img_width * scale
        draw_height = img_height * scale

        draw_x = cell_x + (cell_width - draw_width) / 2
        draw_y = cell_y + (cell_height - draw_height) / 2

        pdf.drawImage(
            image,
            draw_x,
            draw_y,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )

    pdf.save()
    buffer.seek(0)
    return buffer