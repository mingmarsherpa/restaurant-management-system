
from io import BytesIO

import qrcode


def generate_table_qr(url: str) -> BytesIO:
    image = qrcode.make(url)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
