from aiogram import F, Router
from aiogram.types import Message
from services.groq_service import analyze_text

router = Router()

# فقط به پیام‌هایی که ربات رو منشن کرده‌ان یا ریپلی به ربات هستند جواب بده
@router.message(F.text.contains("@OrgKonohaBot") | F.reply_to_message)
async def handle_mention(message: Message):
    user_message = message.text or ""
    user_message = user_message.replace("@OrgKonohaBot", "").strip()
    
    # دریافت پاسخ از Groq
    response = await analyze_text(user_message)
    
    # ارسال پاسخ به صورت ریپلای
    await message.reply(response)

# برای چت خصوصی (بدون منشن)
@router.message(F.chat.type == "private")
async def handle_private(message: Message):
    response = await analyze_text(message.text)
    await message.reply(response)
