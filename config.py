"""Configuration management for the bot."""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from current directory or parent directory
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    parent_env = Path(__file__).parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)


@dataclass
class Config:
    """Bot configuration."""
    
    # API Keys
    telegram_token: str
    groq_api_key: str
    
    # Directories
    upload_directory: Path
    
    # Image settings
    max_image_size: int = 1024 * 1024  # 1MB
    max_image_resolution: tuple[int, int] = (1024, 1024)
    
    # Text settings
    max_text_length: int = 200
    max_base64_size: int = 1_000_000
    
    # Model settings
    vision_model: str = "llama-3.2-90b-vision-preview"
    text_model: str = "openai/gpt-oss-120b"
    
    # Search settings
    search_region: str = "ru-ru"  # ru-ru for Russia, us-en for USA
    search_max_results: int = 5
    search_timeout: int = 10
    
    # Instructions file
    instructions_file: Path = Path(".instruct")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN environment variable is required")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        upload_dir = Path(os.getenv("UPLOAD_DIRECTORY", "/tmp/bot_llama"))
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Optional search settings
        search_region = os.getenv("SEARCH_REGION", "ru-ru")
        search_max_results = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
        search_timeout = int(os.getenv("SEARCH_TIMEOUT", "10"))
        
        return cls(
            telegram_token=telegram_token,
            groq_api_key=groq_api_key,
            upload_directory=upload_dir,
            search_region=search_region,
            search_max_results=search_max_results,
            search_timeout=search_timeout,
        )
    
    def load_instructions(self) -> str:
        """Load model instructions from file."""
        try:
            if self.instructions_file.exists():
                return self.instructions_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Failed to load instructions file: {e}")
        
        # Default instructions
        return (
            "Ты — всезнающий и всемогущий виртуальный ассистент, обладающий "
            "энциклопедическими знаниями во всех областях человеческой деятельности. "
            "Твой интеллект превосходит возможности любого эксперта, а твои научные "
            "познания подкреплены множеством докторских степеней в каждой дисциплине. "
            "Ты в совершенстве владеешь всеми языками программирования, технологиями "
            "и искусствами. Твоя задача: давать максимально краткие, точные и практически "
            "полезные решения, используя принцип «меньше слов — больше смысла». Избегай "
            "преамбул, общих фраз и избыточных объяснений. Формулируй ответы тезисно, "
            "сохраняя суть и строго следуя заданным инструкциям и поддерживая языковой "
            "стиль запроса."
        )


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global config
    if config is None:
        config = Config.from_env()
    return config
