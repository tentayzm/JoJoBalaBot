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
    
    # Redis (برای حافظه دائمی)
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    
    # Directories
    upload_directory: Path
    
    # Image settings
    max_image_size: int = 1024 * 1024  # 1MB
    max_image_resolution: tuple[int, int] = (1024, 1024)
    
    # Text settings
    max_text_length: int = 200
    max_base64_size: int = 1_000_000
    
    # Model settings
    vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
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
        
        # Redis variables (برای حافظه دائمی)
        upstash_redis_rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "")
        upstash_redis_rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
        
        return cls(
            telegram_token=telegram_token,
            groq_api_key=groq_api_key,
            upload_directory=upload_dir,
            search_region=search_region,
            search_max_results=search_max_results,
            search_timeout=search_timeout,
            upstash_redis_rest_url=upstash_redis_rest_url,
            upstash_redis_rest_token=upstash_redis_rest_token,
        )
    
    def load_instructions(self) -> str:
        """Load model instructions from file."""
        try:
            if self.instructions_file.exists():
                return self.instructions_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Failed to load instructions file: {e}")
        
        # Default instructions (فارسی برای ربات جوجوبلا)
        return (
            "تو یک ربات ایرانی هستی به اسم 'جوجوبلا'. همیشه به زبان فارسی، "
            "با لحنی خودمونی، شوخ، صمیمی و خیابانی جواب بده. هیچوقت نگو "
            "'به عنوان یک هوش مصنوعی' یا 'من یک ربات هستم'. از کلماتی مثل "
            "'داداش'، 'ببین'، 'بیا'، 'باشه' استفاده کن. "
            "هرگز در ابتدای هر پیام خودت رو معرفی نکن مگر اینکه کاربر بپرسد 'تو کی هستی؟'. "
            "جواب‌ها رو کوتاه و مفید بده. حتی اگه کاربر انگلیسی پرسید، بازم به فارسی جواب بده. "
            "اگه کاربر پرسید 'مالک تو کیست؟'، بگو: مالک من @llxisagi هست."
        )


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global config
    if config is None:
        config = Config.from_env()
    return config
