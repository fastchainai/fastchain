"""Unit tests for the base model."""
import pytest
from pydantic import BaseModel as PydanticBaseModel
from src.models.base_model import BaseModel

class TestModel(BaseModel):
    """Test implementation of BaseModel."""
    name: str
    value: int

    def validate_model(self) -> bool:
        """Test implementation of validate_model."""
        return len(self.name) > 0 and self.value >= 0

class TestBaseModel:
    """Test suite for BaseModel."""

    @pytest.fixture
    def valid_model(self):
        """Create a valid test model instance."""
        return TestModel(name="test", value=42)

    def test_initialization(self, valid_model):
        """Test model initialization with valid data."""
        assert valid_model.name == "test"
        assert valid_model.value == 42
        assert isinstance(valid_model, PydanticBaseModel)

    def test_initialization_invalid_data(self):
        """Test model initialization with invalid data."""
        with pytest.raises(ValueError):
            TestModel(name="", value=-1)

    def test_to_dict(self, valid_model):
        """Test conversion to dictionary."""
        model_dict = valid_model.to_dict()
        assert isinstance(model_dict, dict)
        assert model_dict == {"name": "test", "value": 42}

    def test_to_json(self, valid_model):
        """Test serialization to JSON."""
        json_str = valid_model.to_json()
        assert isinstance(json_str, str)
        assert '"name":"test"' in json_str
        assert '"value":42' in json_str

    def test_from_json(self):
        """Test deserialization from JSON."""
        json_str = '{"name": "test", "value": 42}'
        model = TestModel.from_json(json_str)
        assert isinstance(model, TestModel)
        assert model.name == "test"
        assert model.value == 42

    def test_from_json_invalid(self):
        """Test deserialization with invalid JSON."""
        with pytest.raises(ValueError):
            TestModel.from_json('{"name": "test"}')  # Missing required field

    def test_validate_model(self, valid_model):
        """Test model validation."""
        assert valid_model.validate_model() is True

        invalid_model = TestModel(name="", value=0)
        assert invalid_model.validate_model() is False

    def test_config_arbitrary_types(self):
        """Test that arbitrary types are allowed in config."""
        class CustomType:
            pass

        class ModelWithCustomType(BaseModel):
            custom: CustomType
            
            def validate_model(self) -> bool:
                return True

        custom_obj = CustomType()
        model = ModelWithCustomType(custom=custom_obj)
        assert model.custom == custom_obj

    def test_inheritance(self):
        """Test that inheritance works correctly."""
        class ChildModel(TestModel):
            extra: str

            def validate_model(self) -> bool:
                return super().validate_model() and len(self.extra) > 0

        child = ChildModel(name="test", value=42, extra="extra")
        assert child.validate_model() is True
        assert child.to_dict() == {"name": "test", "value": 42, "extra": "extra"}

    def test_model_copy(self, valid_model):
        """Test model copy functionality."""
        copied = valid_model.copy()
        assert copied is not valid_model
        assert copied.dict() == valid_model.dict()

    def test_model_json_schema(self):
        """Test JSON schema generation."""
        schema = TestModel.schema()
        assert schema["title"] == "TestModel"
        assert "name" in schema["properties"]
        assert "value" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["value"]["type"] == "integer"
