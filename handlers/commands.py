"""Command handlers."""
import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from keyboards.main_keyboard import get_main_keyboard


logger = logging.getLogger(__name__)
router = Router()

# Global state for reasoning (in production, use FSM or database)
reasoning_state = {"enabled": True}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.reply(
        "Привет! Я бот, который может отвечать на вопросы и анализировать изображения. "
        "Используйте кнопку 'Reasoning On/Off' для управления подробностью ответа.",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("reasoning"))
async def cmd_reasoning(message: Message) -> None:
    """Handle /reasoning command."""
    reasoning_state["enabled"] = not reasoning_state["enabled"]
    status = "включен" if reasoning_state["enabled"] else "выключен"
    
    await message.reply(
        f"Режим рассуждений теперь {status}.",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "Reasoning On/Off")
async def toggle_reasoning(message: Message) -> None:
    """Handle reasoning toggle button."""
    reasoning_state["enabled"] = not reasoning_state["enabled"]
    status = "включен" if reasoning_state["enabled"] else "выключен"
    
    await message.reply(
        f"Режим рассуждений теперь {status}.",
        reply_markup=get_main_keyboard()
    )


def is_reasoning_enabled() -> bool:
    """Check if reasoning is enabled."""
    return reasoning_state["enabled"]