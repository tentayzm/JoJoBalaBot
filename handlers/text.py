from aiogram import F, Router
from aiogram.types import Message
from services.groq_service import GroqService

# ساخت یک نمونه از کلاس GroqService
groq_service = GroqService()

router = Router()

# فقط به پیام‌هایی که ربات رو منشن کرده‌ان یا ریپلی به ربات هستند جواب بده
@router.message(F.text.contains("@OrgKonohaBot") | F.reply_to_message)
async def handle_mention(message: Message):
    user_message = message.text or ""
    user_message = user_message.replace("@OrgKonohaBot", "").strip()
    
    # ساخت لیست messages برای ارسال به متد analyze_text
    messages = [{"role": "user", "content": user_message}]
    
    # دریافت پاسخ از Groq
    response = await groq_service.analyze_text(messages)
    
    # ارسال پاسخ به صورت ریپلای (با تقسیم به چند پیام اگه طولانی بود)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.reply(response[i:i+4000])
    else:
        await message.reply(response)

# برای چت خصوصی (بدون منشن)
@router.message(F.chat.type == "private")
async def handle_private(message: Message):
    messages = [{"role": "user", "content": message.text}]
    response = await groq_service.analyze_text(messages)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await message.reply(response[i:i+4000])
    else:
        await message.reply(response)
