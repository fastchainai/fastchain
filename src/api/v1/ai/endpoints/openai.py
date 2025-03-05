"""OpenAI endpoints for text generation and analysis."""
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.models.openai_model import OpenAIModel

logger = logging.getLogger(__name__)
router = APIRouter()

class TextGenerationRequest(BaseModel):
    """Schema for text generation request."""
    prompt: str = Field(..., description="Input prompt for text generation")
    max_tokens: Optional[int] = Field(150, description="Maximum number of tokens to generate")

class SentimentAnalysisRequest(BaseModel):
    """Schema for sentiment analysis request."""
    text: str = Field(..., description="Text to analyze for sentiment")

@router.post("/generate", response_model=Dict[str, Any], tags=["AI Generation"])
async def generate_text(request: TextGenerationRequest) -> Dict[str, Any]:
    """
    Generate text using OpenAI's GPT model.
    """
    try:
        model = OpenAIModel()
        result = await model.generate_text(request.prompt, request.max_tokens)
        return result
    except Exception as e:
        logger.error(f"[OpenAI Endpoint] Text generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/sentiment", response_model=Dict[str, Any], tags=["AI Analysis"])
async def analyze_sentiment(request: SentimentAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze sentiment of input text.
    """
    try:
        model = OpenAIModel()
        result = await model.analyze_sentiment(request.text)
        return result
    except Exception as e:
        logger.error(f"[OpenAI Endpoint] Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
