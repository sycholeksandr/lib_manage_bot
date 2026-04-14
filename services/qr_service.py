from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr_code_with_book_id(data: str, book_id: int) -> BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    text = f"ID: {book_id}"

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    dummy_image = Image.new("RGB", (1, 1), "white")
    draw = ImageDraw.Draw(dummy_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)

    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    qr_width, qr_height = qr_image.size

    padding_top = 10
    padding_bottom = 20
    spacing = 15

    final_width = max(qr_width, text_width + 40)
    final_height = qr_height + spacing + text_height + padding_top + padding_bottom

    final_image = Image.new("RGB", (final_width, final_height), "white")
    final_draw = ImageDraw.Draw(final_image)

    qr_x = (final_width - qr_width) // 2
    qr_y = padding_top
    final_image.paste(qr_image, (qr_x, qr_y))

    text_x = (final_width - text_width) // 2
    text_y = qr_y + qr_height + spacing
    final_draw.text((text_x, text_y), text, fill="black", font=font)

    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer