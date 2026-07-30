"""Placeholder handlers for features under development."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_main_menu_keyboard
from services.user_service import UserService

router = Router()
