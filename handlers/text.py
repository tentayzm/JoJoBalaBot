from aiogram import F, Router
from aiogram.types import Message
from services.groq_service import GroqService

groq_service = GroqService()
router = Router()

# فقط به کلمه "جوجوبلا" یا ریپلای جواب بده
@router.message((F.text.lower() == "جوجوبلا") | F.reply_to_message)
async def handle_mention(message: Message):
    # جلوگیری از ریپلای زنجیره‌ای (جواب دادن به ریپلای خود ربات)
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        return  # هیچ جوابی نده
    
    user_message = message.text or ""
    if user_message.lower() == "جوجوبلا":
        user_message = "سلام داداش، جوجوبلا اینجاست!"
    
    messages = [{"role": "user", "content": user_message}]
    response = await groq_service.analyze_text(
        messages, 
        chat_id=message.chat.id, 
        user_id=message.from_user.id
    )
    
    # تقسیم پاسخ بلند
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.reply(response[i:i+4000])
    else:
        await message.reply(response)

# برای چت خصوصی (هر پیامی جواب بده)
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
