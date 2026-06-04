"""Image processing utilities."""
import base64
import logging
from pathlib import Path

from PIL import Image

from config import get_config


logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities."""
    
    def __init__(self):
        """Initialize image processor."""
        self.config = get_config()
    
    def encode_image(self, image_path: Path) -> str:
        """
        Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def reduce_image_size(
        self,
        input_path: Path,
        output_path: Path
    ) -> None:
        """
        Reduce image size and resolution.
        
        Args:
            input_path: Input image path
            output_path: Output image path
        """
        img = Image.open(input_path)
        img_size = input_path.stat().st_size
        
        if img_size > self.config.max_image_size:
            # Reduce resolution
            img.thumbnail(self.config.max_image_resolution)
            img.save(output_path, format='JPEG', quality=80, optimize=True)
            
            final_size = output_path.stat().st_size
            logger.info(
                f"Image compressed from {img_size} to {final_size} bytes "
                f"with resolution {img.size}"
            )
        else:
            # Just convert to JPEG
            img.save(output_path, format='JPEG')