"""Test provider support and model configuration."""
import pytest
from cmdsaw.parsing.llm_parser import _build_model
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI


def test_build_ollama_model():
    """Test that Ollama model is built correctly."""
    model = _build_model("gemma3:12b", provider="ollama", temperature=0.5)
    
    assert isinstance(model, ChatOllama)
    assert model.model == "gemma3:12b"
    assert model.temperature == 0.5


def test_build_google_model_with_api_key():
    """Test that Google model is built correctly with API key."""
    # Use a fake API key for testing (won't actually call the API)
    fake_api_key = "test-api-key-12345"
    
    model = _build_model(
        "gemini-pro", 
        provider="google", 
        temperature=0.7,
        google_api_key=fake_api_key
    )
    
    assert isinstance(model, ChatGoogleGenerativeAI)
    # Google models add "models/" prefix
    assert model.model == "models/gemini-pro"
    assert model.temperature == 0.7


def test_build_google_model_without_api_key_raises_error():
    """Test that Google model without API key raises ValueError."""
    with pytest.raises(ValueError, match="Google API key is required"):
        _build_model("gemini-pro", provider="google", temperature=0.5)


def test_build_model_with_invalid_provider_raises_error():
    """Test that invalid provider raises ValueError."""
    with pytest.raises(ValueError, match="Unknown provider"):
        _build_model("some-model", provider="invalid", temperature=0.5)


def test_ollama_model_with_zero_temperature():
    """Test Ollama model with deterministic temperature."""
    model = _build_model("gemma3:12b", provider="ollama", temperature=0.0)
    
    assert isinstance(model, ChatOllama)
    assert model.temperature == 0.0


def test_google_model_with_zero_temperature():
    """Test Google model with deterministic temperature."""
    fake_api_key = "test-api-key-12345"
    
    model = _build_model(
        "gemini-pro", 
        provider="google", 
        temperature=0.0,
        google_api_key=fake_api_key
    )
    
    assert isinstance(model, ChatGoogleGenerativeAI)
    assert model.temperature == 0.0


if __name__ == '__main__':
    test_build_ollama_model()
    print("✓ test_build_ollama_model passed")
    
    test_build_google_model_with_api_key()
    print("✓ test_build_google_model_with_api_key passed")
    
    test_build_google_model_without_api_key_raises_error()
    print("✓ test_build_google_model_without_api_key_raises_error passed")
    
    test_build_model_with_invalid_provider_raises_error()
    print("✓ test_build_model_with_invalid_provider_raises_error passed")
    
    test_ollama_model_with_zero_temperature()
    print("✓ test_ollama_model_with_zero_temperature passed")
    
    test_google_model_with_zero_temperature()
    print("✓ test_google_model_with_zero_temperature passed")
    
    print("\nAll tests passed!")
