"""Base model providing foundation for all models in the system."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.utils.logging import Logging
from pydantic import BaseModel as PydanticBaseModel

# Set up logging
logger = Logging(__name__)

class BaseModel(PydanticBaseModel, ABC):
    """
    BaseModel provides a foundation for all models, extending Pydantic's BaseModel
    with additional functionality.
    """

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        """
        return self.dict()

    def to_json(self) -> str:
        """
        Serialize the model instance to a JSON string.
        """
        return self.json()

    @classmethod
    def from_json(cls, json_str: str) -> "BaseModel":
        """
        Create an instance of the model from a JSON string.
        """
        return cls.parse_raw(json_str)

    @abstractmethod
    def validate_model(self) -> bool:
        """
        Abstract method for model-specific validation.
        Must be implemented by subclasses.
        """
        pass