"""Photo message handlers."""
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from services.groq_service import GroqService
from utils.image_processor import ImageProcessor
from utils.message_splitter import MessageSplitter
from keyboards.main_keyboard import get_main_keyboard
from config import get_config


logger = logging.getLogger(__name__)
router = Router()


async def safe_delete_message(message: Message) -> None:
    """
    Safely delete a message, ignoring errors.
    
    Args:
        message: Message to delete
    """
    try:
        await message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Could not delete message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting message: {e}")


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Handle photo messages."""
    config = get_config()
    user_text = message.caption if message.caption else "Проанализируй это изображение."
    
    # Get largest photo
    photo = message.photo[-1]
    
    # Generate file paths
    file_name = f"{message.from_user.id}_{photo.file_unique_id}.jpg"
    file_path = config.upload_directory / file_name
    compressed_path = config.upload_directory / f"compressed_{file_name}"
    
    # Send status message
    status_msg = await message.answer("Запрос получен, анализирую...")
    
    try:
        # Download photo
        await message.bot.download(
            file=photo.file_id,
            destination=file_path
        )
        
        # Process image
        image_processor = ImageProcessor()
        image_processor.reduce_image_size(file_path, compressed_path)
        
        # Encode image
        base64_image = image_processor.encode_image(compressed_path)
        
        # Analyze image
        groq_service = GroqService()
        result = await groq_service.analyze_image(base64_image, user_text)
        
        # Delete status message safely
        await safe_delete_message(status_msg)
        
        # Split message if too long and send
        message_chunks = MessageSplitter.split_message(result)
        
        for idx, chunk in enumerate(message_chunks):
            try:
                # Only add keyboard to the last message
                keyboard = get_main_keyboard() if idx == len(message_chunks) - 1 else None
                
                await message.answer(chunk, reply_markup=keyboard)
            except TelegramBadRequest as e:
                logger.error(f"Failed to send chunk {idx + 1}: {e}")
                await message.answer(
                    f"Часть {idx + 1}: [Не удалось отправить]",
                    reply_markup=keyboard
                )
        
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        await safe_delete_message(status_msg)
        await message.reply(f"Ошибка: {ve}", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error analyzing image: {e}", exc_info=True)
        await safe_delete_message(status_msg)
        await message.reply(
            "Произошла ошибка при анализе изображения.",
            reply_markup=get_main_keyboard()
        )
        
    finally:
        # Cleanup files
        for path in [file_path, compressed_path]:
            if path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete file {path}: {e}")