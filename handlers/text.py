"""Text message handlers."""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from services.groq_service import GroqService
from services.search_service import SearchService
from keyboards.main_keyboard import get_main_keyboard
from handlers.commands import is_reasoning_enabled
from utils.message_splitter import MessageSplitter
from config import get_config


logger = logging.getLogger(__name__)
router = Router()

# Conversation history (in production, use database or FSM)
conversation_history = {}


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


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Handle text messages."""
    user_id = message.from_user.id
    text = " ".join(message.text.split())
    
    # Initialize user's conversation history
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Add user message to history
    conversation_history[user_id].append({
        "role": "user",
        "content": text
    })
    
    # Keep only last 6 messages
    if len(conversation_history[user_id]) > 6:
        conversation_history[user_id] = conversation_history[user_id][-6:]
    
    # Send initial response
    status_msg = await message.answer("Запрос получен, анализирую...")
    
    try:
        groq_service = GroqService()
        config = get_config()
        
        # Check if query ends with '?' - perform web search
        if text.strip().endswith('?'):
            logger.info(f"Performing web search for query: {text}")
            
            # Initialize SearchService with config settings
            search_service = SearchService(
                max_results=config.search_max_results,
                region=config.search_region,
                timeout=config.search_timeout
            )
            search_results = await search_service.search(text)
            
            if search_results:
                # Get AI response with search context
                response_content = await groq_service.analyze_with_search(
                    query=text,
                    search_results=search_results,
                    conversation_history=conversation_history[user_id][:-1]
                )
            else:
                response_content = (
                    "Не удалось получить результаты поиска. "
                    "Попробуйте изменить запрос или повторить позже."
                )
        else:
            # Regular text analysis
            response_content = await groq_service.analyze_text(
                conversation_history[user_id]
            )
        
        # Process response based on reasoning mode
        if is_reasoning_enabled():
            final_response = response_content
        else:
            # Remove thinking tags
            final_response = re.sub(
                r'<think>.*?</think>',
                '',
                response_content,
                flags=re.DOTALL
            ).strip()
        
        # Delete status message safely
        await safe_delete_message(status_msg)
        
        # Split message if too long and send
        message_chunks = MessageSplitter.split_message(final_response)
        
        for idx, chunk in enumerate(message_chunks):
            try:
                # Only add keyboard to the last message
                keyboard = get_main_keyboard() if idx == len(message_chunks) - 1 else None
                
                await message.answer(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            except TelegramBadRequest as e:
                logger.error(f"Failed to send chunk {idx + 1} with Markdown: {e}")
                # Try without markdown parsing
                await message.answer(
                    chunk,
                    reply_markup=keyboard
                )
        
        # Add assistant response to history
        conversation_history[user_id].append({
            "role": "assistant",
            "content": response_content
        })
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        await safe_delete_message(status_msg)
        
        error_message = f"Произошла ошибка при обработке запроса: {str(e)}"
        
        try:
            await message.reply(
                error_message,
                reply_markup=get_main_keyboard()
            )
        except TelegramBadRequest:
            # If reply fails, just send a simple message
            await message.answer("Произошла ошибка при обработке запроса.")