"""DuckDuckGo search service using ddgs library."""
import logging
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException


logger = logging.getLogger(__name__)


class SearchService:
    """Service for performing web searches using DuckDuckGo via ddgs library."""
    
    def __init__(
        self,
        max_results: int = 5,
        region: str = "ru-ru",
        timeout: int = 10
    ):
        """
        Initialize search service.
        
        Args:
            max_results: Maximum number of search results
            region: Search region (ru-ru for Russia, us-en for USA, etc.)
            timeout: Timeout for search requests
        """
        self.max_results = max_results
        self.region = region
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=3)
    
    def _perform_search_sync(self, query: str) -> List[Dict[str, Any]]:
        """
        Synchronous search method (to be run in executor).
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"Performing DDGS search for: {query}")
            
            # Initialize DDGS with timeout
            ddgs = DDGS(timeout=self.timeout)
            
            # Perform text search
            # text() returns a list directly, not an iterator
            search_results = ddgs.text(
                query=query,
                region=self.region,
                safesearch="moderate",
                timelimit=None,
                max_results=self.max_results,
                backend="auto"
            )
            
            # Format results
            results = []
            for idx, result in enumerate(search_results, 1):
                results.append({
                    "number": idx,
                    "title": result.get("title", ""),
                    "link": result.get("href", ""),
                    "body": result.get("body", "")
                })
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except RatelimitException as e:
            logger.error(f"Rate limit exceeded: {e}")
            return []
        except TimeoutException as e:
            logger.error(f"Search timeout: {e}")
            return []
        except DDGSException as e:
            logger.error(f"DDGS error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected search error: {e}", exc_info=True)
            return []
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a web search asynchronously.
        
        Args:
            query: Search query
            
        Returns:
            List of search results with title, link, and body
        """
        # Run synchronous search in executor to avoid blocking
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self._executor,
            self._perform_search_sync,
            query
        )
        return results
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for display.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string with search results
        """
        if not results:
            return "Результаты поиска не найдены."
        
        formatted = "🔍 **Результаты поиска:**\n\n"
        
        for result in results:
            formatted += f"{result['number']}. **{result['title']}**\n"
            formatted += f"🔗 {result['link']}\n"
            
            # Truncate body if too long
            body = result['body']
            if len(body) > 200:
                body = body[:200] + "..."
            formatted += f"📝 {body}\n\n"
        
        return formatted
    
    async def search_news(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a news search.
        
        Args:
            query: Search query
            
        Returns:
            List of news results
        """
        try:
            logger.info(f"Performing DDGS news search for: {query}")
            
            loop = asyncio.get_event_loop()
            
            def _search_news():
                ddgs = DDGS(timeout=self.timeout)
                return ddgs.news(
                    query=query,
                    region=self.region,
                    safesearch="moderate",
                    timelimit="w",  # Last week
                    max_results=self.max_results,
                    backend="auto"
                )
            
            news_results = await loop.run_in_executor(
                self._executor,
                _search_news
            )
            
            # Format results
            results = []
            for idx, result in enumerate(news_results, 1):
                results.append({
                    "number": idx,
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "body": result.get("body", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", "")
                })
            
            logger.info(f"Found {len(results)} news results")
            return results
            
        except Exception as e:
            logger.error(f"News search error: {e}", exc_info=True)
            return []
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)