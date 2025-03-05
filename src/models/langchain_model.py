# src/models/langchain_model.py
"""LangChain model implementation extending the base model."""

from .base_model import BaseModel
from typing import Dict, Any, Optional

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class LangChainModel(BaseModel):
    """
    LangChainModel extends BaseModel to provide LangChain functionality.
    """
    model_temperature: float = 0.0
    _llm: Optional[ChatOpenAI] = None
    _prompt: Optional[PromptTemplate] = None

    def __init__(self, **data):
        """Initialize the model with optional configuration."""
        super().__init__(**data)
        self._setup_default_chain()

    def _setup_default_chain(self):
        """Set up default processing components."""
        self._llm = ChatOpenAI(temperature=self.model_temperature)
        self._prompt = PromptTemplate(
            input_variables=["input_text"],
            template="Process the following text: {input_text}"
        )

    def validate_model(self) -> bool:
        """Validate that the model has properly configured components."""
        return self._llm is not None and self._prompt is not None

    def run(self, input_text: str, additional_inputs: Optional[Dict[str, Any]] = None) -> str:
        """
        Process input through the model.

        Args:
            input_text: Primary input text
            additional_inputs: Optional additional variables

        Returns:
            Processed output from the model
        """
        if not self.validate_model():
            raise ValueError("Model components not properly initialized")

        inputs = {"input_text": input_text}
        if additional_inputs:
            inputs.update(additional_inputs)

        # Format prompt with inputs
        formatted_prompt = self._prompt.format(**inputs)

        # Invoke the LLM
        messages = [{"role": "user", "content": formatted_prompt}]
        response = self._llm.invoke(messages)

        return response.content if hasattr(response, 'content') else str(response)