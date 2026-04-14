from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
