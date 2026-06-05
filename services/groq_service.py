"""Groq API service for LLM interactions."""
import logging
import json
from typing import List, Dict, Any

from groq import Groq
from upstash_redis import Redis

from config import get_config


logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API with Redis memory."""
    
    def __init__(self):
        """Initialize Groq service."""
        self.config = get_config()
        self.client = Groq(api_key=self.config.groq_api_key)
        self.instructions = self.config.load_instructions()
        
        # پرامپت سیستمی (شخصیت جوجوبلا + معرفی مالک)
        self.system_prompt = (
            "تو یک ربات ایرانی هستی به اسم 'جوجوبلا'. همیشه به زبان فارسی، "
            "با لحنی خودمونی، شوخ، صمیمی و خیابانی جواب بده. هیچوقت نگو "
            "'به عنوان یک هوش مصنوعی' یا 'من یک ربات هستم'. از کلماتی مثل "
            "'داداش'، 'ببین'، 'بیا'، 'باشه' استفاده کن. "
            "هرگز در ابتدای هر پیام خودت رو معرفی نکن مگر اینکه کاربر بپرسد 'تو کی هستی؟'. "
            "جواب‌ها رو کوتاه و مفید بده. حتی اگه کاربر انگلیسی پرسید، بازم به فارسی جواب بده. "
            "اگه کاربر پرسید 'مالک تو کیست؟'، 'سازنده تو کیه؟'، 'متعلق به کدام تیم هستی؟' یا سوالات مشابه، بگو: "
            "مالک من @llxisagi هست. ایشون کدهای منو نوشتن و به یه طوری پدر من به حساب میان. مدت‌ها زمان گذاشتن منو بسازن و برای من خیلی قابل احترام هستن."
        )
        
        # اتصال به Redis (حافظه دائمی)
        try:
            self.redis = Redis(
                url=self.config.upstash_redis_rest_url,
                token=self.config.upstash_redis_rest_token
            )
            logger.info("Connected to Upstash Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Memory will be lost on restart.")
            self.redis = None
    
    async def get_history(self, chat_id: str, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """گرفتن تاریخچه مکالمه از Redis"""
        if not self.redis:
            return []
        
        key = f"chat:{chat_id}:{user_id}"
        try:
            messages_json = self.redis.lrange(key, -limit, -1)
            history = [json.loads(msg) for msg in messages_json]
            logger.info(f"Loaded {len(history)} messages from Redis for {chat_id}/{user_id}")
            return history
        except Exception as e:
            logger.error(f"Error loading history from Redis: {e}")
            return []
    
    async def save_to_history(self, chat_id: str, user_id: str, role: str, content: str, max_history: int = 50):
        """ذخیره پیام در Redis (حداکثر max_history پیام)"""
        if not self.redis:
            return
        
        key = f"chat:{chat_id}:{user_id}"
        message = json.dumps({"role": role, "content": content})
        try:
            self.redis.rpush(key, message)
            self.redis.ltrim(key, -max_history, -1)
            self.redis.expire(key, 60*60*24*30)  # 30 روز
            logger.debug(f"Saved message for {chat_id}/{user_id}")
        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")
    
    async def analyze_text(
        self,
        messages: List[Dict[str, str]],
        chat_id: str = None,
        user_id: str = None,
        temperature: float = 0
    ) -> str:
        """Analyze text using Groq API with Redis memory."""
        try:
            # ساخت تاریخچه کامل
            full_history = []
            user_msg = ""
            
            # 1. پرامپت سیستمی
            full_history.append({"role": "system", "content": self.system_prompt})
            
            # 2. تاریخچه قبلی از Redis
            if chat_id and user_id:
                history = await self.get_history(str(chat_id), str(user_id), limit=30)
                full_history.extend(history)
                
                if messages and messages[-1].get("role") == "user":
                    user_msg = messages[-1].get("content", "")
                    await self.save_to_history(str(chat_id), str(user_id), "user", user_msg, max_history=50)
            
            # 3. پیام جدید کاربر
            full_history.extend(messages)
            
            logger.info(f"Sending text analysis request to Groq (history length: {len(full_history)})")
            
            response = self.client.chat.completions.create(
                model=self.config.text_model,
                messages=full_history,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            logger.info("Received response from Groq")
            
            # ذخیره پاسخ در Redis
            if chat_id and user_id and content:
                await self.save_to_history(str(chat_id), str(user_id), "assistant", content, max_history=50)
            
            return content
            
        except Exception as e:
            logger.error(f"Groq text analysis error: {e}", exc_info=True)
            raise
    
    # ========== بقیه متدها (analyze_image, analyze_with_search) ==========
    async def analyze_image(
        self,
        base64_image: str,
        user_text: str
    ) -> str:
        """Analyze image using Groq vision model."""
        try:
            if len(user_text) > self.config.max_text_length:
                user_text = user_text[:self.config.max_text_length]
            
            if len(base64_image) > self.config.max_base64_size:
                raise ValueError("Base64 image too large for API.")
            
            logger.info("Sending image analysis request to Groq")
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{self.instructions}\n\n{user_text}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                model=self.config.vision_model,
            )
            
            content = chat_completion.choices[0].message.content
            logger.info("Received image analysis response from Groq")
            return content
            
        except Exception as e:
            logger.error(f"Groq image analysis error: {e}", exc_info=True)
            raise
    
    async def analyze_with_search(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Analyze query with search results context."""
        search_context = "\n\n".join([
            f"Источник {r['number']}: {r['title']}\n{r['body']}"
            for r in search_results
        ])
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + conversation_history + [
            {
                "role": "user",
                "content": (
                    f"Вот результаты поиска по запросу '{query}':\n\n"
                    f"{search_context}\n\n"
                    f"Проанализируй данные и дай развернутый ответ на запрос, "
                    f"используя следующие инструкции: {self.instructions}"
                )
            }
        ]
        
        return await self.analyze_text(messages)
