"""Main bot keyboards."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Get main bot keyboard.
    
    Returns:
        Main keyboard with reasoning toggle
    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Reasoning On/Off"))
    
    return builder.as_markup(resize_keyboard=True)