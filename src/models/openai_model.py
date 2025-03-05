"""OpenAI model integration module."""
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIModel:
    """OpenAI model wrapper for API interactions."""

    def __init__(self):
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            logger.info("[OpenAI Model] Successfully initialized OpenAI client")
        except Exception as e:
            logger.error(f"[OpenAI Model] Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")

    async def generate_text(self, prompt: str, max_tokens: Optional[int] = 150) -> Dict[str, Any]:
        """
        Generate text using OpenAI's GPT model.

        Args:
            prompt: The input prompt for text generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            Dict containing the generated text and metadata
        """
        try:
            # Use gpt-4o which was released May 13, 2024
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            
            return {
                "text": response.choices[0].message.content,
                "metadata": {
                    "model": "gpt-4o",
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens": {
                        "completion": response.usage.completion_tokens,
                        "prompt": response.usage.prompt_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            }
        except Exception as e:
            logger.error(f"[OpenAI Model] Text generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {str(e)}")

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of input text using OpenAI model.

        Args:
            text: Text to analyze

        Returns:
            Dict containing sentiment analysis results
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze the sentiment of the text and provide a rating from 1 to 5 stars and a confidence score between 0 and 1."
                    },
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return {
                "sentiment": result,
                "metadata": {
                    "model": "gpt-4o",
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens": {
                        "completion": response.usage.completion_tokens,
                        "prompt": response.usage.prompt_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            }
        except Exception as e:
            logger.error(f"[OpenAI Model] Sentiment analysis failed: {e}")
            raise RuntimeError(f"Sentiment analysis failed: {str(e)}")
