"""Groq API service for LLM interactions."""
import logging
from typing import List, Dict, Any

from groq import Groq

from config import get_config


logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API."""
    
    def __init__(self):
        """Initialize Groq service."""
        self.config = get_config()
        self.client = Groq(api_key=self.config.groq_api_key)
        self.instructions = self.config.load_instructions()
    
    async def analyze_text(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0
    ) -> str:
        """
        Analyze text using Groq API.
        
        Args:
            messages: List of chat messages
            temperature: Model temperature
            
        Returns:
            Model response
        """
        try:
            logger.info("Sending text analysis request to Groq")
            
            response = self.client.chat.completions.create(
                model=self.config.text_model,
                messages=messages,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            logger.info("Received response from Groq")
            return content
            
        except Exception as e:
            logger.error(f"Groq text analysis error: {e}", exc_info=True)
            raise
    
    async def analyze_image(
        self,
        base64_image: str,
        user_text: str
    ) -> str:
        """
        Analyze image using Groq vision model.
        
        Args:
            base64_image: Base64 encoded image
            user_text: User's text prompt
            
        Returns:
            Model response
        """
        try:
            # Validate input sizes
            if len(user_text) > self.config.max_text_length:
                user_text = user_text[:self.config.max_text_length]
            
            if len(base64_image) > self.config.max_base64_size:
                raise ValueError(
                    "Base64 строка слишком длинная, изображение слишком большое для API."
                )
            
            logger.info("Sending image analysis request to Groq")
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{self.instructions}\n\n{user_text}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
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
        """
        Analyze query with search results context.
        
        Args:
            query: User query
            search_results: Search results from DuckDuckGo
            conversation_history: Previous conversation messages
            
        Returns:
            Model response
        """
        # Format search results for context
        search_context = "\n\n".join([
            f"Источник {r['number']}: {r['title']}\n{r['body']}"
            for r in search_results
        ])
        
        # Build messages with search context
        messages = conversation_history + [
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