# Oseredok Library Bot

Telegram-Bot for library managing.

## Main features

- users registration
- borrowing and returning of books using deep link / QR
- admin-panel
- book adding, editing and deleting
- QR-Codes generation for books

## Stack

- Python
- aiogram
- PostgreSQL
- SQLAlchemy (async)
- pytest
- qrcode / Pillow

## Setup

1. Create and activate virtual environment
2. Setup dependencies:

```bash
pip install -r requirements.txt
```

3. Create .env file, based on .env.example
4. Run the bot

```bash
python ./main.py
```