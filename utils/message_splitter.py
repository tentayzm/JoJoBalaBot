"""Message splitting utilities for Telegram."""
from typing import List


class MessageSplitter:
    """Utility for splitting long messages."""
    
    # Telegram message limit
    MAX_MESSAGE_LENGTH = 4096
    
    @staticmethod
    def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
        """
        Split long message into chunks.
        
        Args:
            text: Text to split
            max_length: Maximum length per message
            
        Returns:
            List of message chunks
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If single paragraph is too long, split by sentences
            if len(paragraph) > max_length:
                sentences = paragraph.split('. ')
                
                for sentence in sentences:
                    # If single sentence is too long, split by words
                    if len(sentence) > max_length:
                        words = sentence.split(' ')
                        
                        for word in words:
                            if len(current_chunk) + len(word) + 1 <= max_length:
                                current_chunk += word + ' '
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                current_chunk = word + ' '
                    else:
                        if len(current_chunk) + len(sentence) + 2 <= max_length:
                            current_chunk += sentence + '. '
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence + '. '
            else:
                if len(current_chunk) + len(paragraph) + 2 <= max_length:
                    current_chunk += paragraph + '\n\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_length]]