from aiogram import F, Router, types
from aiogram.types import Message
from services.groq_service import get_ai_response

router = Router()

# فقط به پیام‌هایی که ربات رو منشن کرده‌ان یا ریپلی به ربات هستند جواب بده
@router.message(F.text.contains("@OrgKonohaBot") | F.reply_to_message)
async def handle_mention(message: Message):
    user_message = message.text or ""
    
    # حذف منشن از متن پیام (اختیاری)
    user_message = user_message.replace("@OrgKonohaBot", "").strip()
    
    # گرفتن جواب از Groq
    response = await get_ai_response(user_message)
    
    # ارسال جواب با ریپلای به پیام کاربر (مهم!)
    await message.reply(response)

# برای چت خصوصی (بدون منشن)
@router.message(F.chat.type == "private")
async def handle_private(message: Message):
    response = await get_ai_response(message.text)
    await message.reply(response)  # اینجا هم ریپلای می‌کنه
