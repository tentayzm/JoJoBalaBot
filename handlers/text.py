from aiogram import F, Router
from aiogram.types import Message
from services.groq_service import GroqService

groq_service = GroqService()
router = Router()

# آیدی عددی ربات (از توکن)
BOT_ID = 8600933235

@router.message(
    (F.text.contains("@OrgKonohaBot")) |
    (F.text.lower() == "جوجوبلا") |
    F.reply_to_message
)
async def handle_message(message: Message):
    # اگه ریپلای شده به پیام خود کاربر (نه ربات)، جواب نده
    if message.reply_to_message and message.reply_to_message.from_user.id != BOT_ID:
        return
    
    user_message = message.text or ""
    user_message = user_message.replace("@OrgKonohaBot", "").strip()
    
    if user_message.lower() == "جوجوبلا":
        user_message = "سلام داداش، من جوجوبلام! چطور می‌تونم کمکت کنم؟"
    
    messages = [{"role": "user", "content": user_message}]
    response = await groq_service.analyze_text(
        messages, 
        chat_id=message.chat.id, 
        user_id=message.from_user.id
    )
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.reply(response[i:i+4000])
    else:
        await message.reply(response)

# چت خصوصی
@router.message(F.chat.type == "private")
async def handle_private(message: Message):
    messages = [{"role": "user", "content": message.text}]
    response = await groq_service.analyze_text(
        messages, 
        chat_id=message.chat.id, 
        user_id=message.from_user.id
    )
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.reply(response[i:i+4000])
    else:
        await message.reply(response)
