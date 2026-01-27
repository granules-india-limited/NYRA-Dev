"""
LLM API interface for making calls to various language models.

This module provides a unified interface for making API calls to different LLM providers
using LiteLLM with simplified error handling and clean parameter management.
"""

from typing import Union, Dict, Any, Optional, AsyncGenerator, List
import os
import json
import litellm
from litellm.router import Router
from litellm.files.main import ModelResponse
from core.utils.logger import logger
from core.utils.config import config
from core.agentpress.error_processor import ErrorProcessor
from pathlib import Path
from datetime import datetime, timezone

# Configure LiteLLM
litellm.modify_params = True
litellm.drop_params = True
# Set num_retries to 1 if not already set via environment variable
if os.environ.get("LITELLM_NUM_RETRIES") is None:
    litellm.num_retries = 1

# Configure Braintrust callback for tracing if API key is set
if os.getenv("BRAINTRUST_API_KEY"):
    litellm.callbacks = ["braintrust"]

provider_router = None
class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass


def setup_api_keys() -> None:
    """Set up provider-specific API configurations."""
    if not config:
        return
    
    # Remove any OpenRouter env vars to prevent LiteLLM from auto-routing to OpenRouter
    # We only use the custom local LLM server
    if 'OPENROUTER_API_KEY' in os.environ:
        del os.environ['OPENROUTER_API_KEY']
    if 'OPENROUTER_API_BASE' in os.environ:
        del os.environ['OPENROUTER_API_BASE']
    
    # AWS Bedrock bearer token
    if getattr(config, 'AWS_BEARER_TOKEN_BEDROCK', None):
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = config.AWS_BEARER_TOKEN_BEDROCK

def setup_provider_router(openai_compatible_api_key: str = None, openai_compatible_api_base: str = None):
    """Configure LiteLLM Router to use custom local LLM server."""
    global provider_router
    
    # Get custom endpoint configuration
    custom_api_base = openai_compatible_api_base or getattr(config, 'OPENAI_COMPATIBLE_API_BASE', None)
    custom_api_key = openai_compatible_api_key or getattr(config, 'OPENAI_COMPATIBLE_API_KEY', None)
    
    if not custom_api_base:
        raise ValueError("OPENAI_COMPATIBLE_API_BASE must be configured to use local LLM server")
    
    # Set API key for LiteLLM - use placeholder if not provided (some endpoints don't require it)
    # LiteLLM requires api_key to be set, even if empty
    api_key_for_litellm = custom_api_key if custom_api_key else "not-required"
    
    # Also set as environment variable for LiteLLM
    os.environ["OPENAI_API_KEY"] = api_key_for_litellm
    
    # Model list: route ALL models to the custom OpenAI-compatible endpoint
    # For OpenAI-compatible endpoints, use "openai/*" in router config
    # The actual model ID will be passed in the request params
    # IMPORTANT: Put specific patterns FIRST so router catches them before wildcard
    model_list = [
        {
            "model_name": "openrouter/*",  # Catch openrouter models FIRST (before auto-detection)
            "litellm_params": {
                "model": "openai/*",  # OpenAI-compatible format
                "api_key": api_key_for_litellm,
                "api_base": custom_api_base,
            },
        },
        {
            "model_name": "openai-compatible/*",  # Catch openai-compatible/* explicitly
            "litellm_params": {
                "model": "openai/*",  # OpenAI-compatible format
                "api_key": api_key_for_litellm,
                "api_base": custom_api_base,
            },
        },
        {
            "model_name": "*",  # Catch all other models
            "litellm_params": {
                "model": "openai/*",  # OpenAI-compatible format
                "api_key": api_key_for_litellm,
                "api_base": custom_api_base,
            },
        },
    ]
    
    # No fallbacks needed - everything goes to the custom endpoint
    fallbacks = []
    
    # Use configured num_retries or default to 1
    num_retries = getattr(litellm, 'num_retries', 1)
    
    provider_router = Router(
        model_list=model_list,
        num_retries=num_retries,
        fallbacks=fallbacks,
    )
    
    logger.info(f"✅ LiteLLM Router configured to use custom local LLM server: {custom_api_base}")

def _configure_openai_compatible(model_name: str, api_key: Optional[str], api_base: Optional[str]) -> None:
    """Configure OpenAI-compatible provider if needed."""
    # This function is no longer used - we bypass the router completely
    # Keeping it for backward compatibility but it does nothing
    pass

def _save_debug_input(params: Dict[str, Any]) -> None:
    """Save LLM input to debug file if enabled."""
    if not (config and getattr(config, 'DEBUG_SAVE_LLM_IO', False)):
        return
    
    try:
        debug_dir = Path("debug_streams")
        debug_dir.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        debug_file = debug_dir / f"input_{timestamp}.json"
        
        debug_data = {k: params.get(k) for k in 
            ["model", "messages", "temperature", "max_tokens", "stop", "stream", "tools", "tool_choice"]}
        debug_data["timestamp"] = timestamp
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        logger.info(f"📁 Saved LLM input to: {debug_file}")
    except Exception as e:
        logger.warning(f"⚠️ Error saving debug input: {e}")

# Internal message properties that should NOT be sent to LLMs
# These are used for internal tracking (compression, expand-message tool, etc.)
_INTERNAL_MESSAGE_PROPERTIES = {"message_id"}

def _strip_internal_properties(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Strip internal properties from messages before sending to LLM.
    
    Some providers (e.g., Groq) reject messages with unknown properties.
    We add properties like 'message_id' for internal tracking but must remove them before LLM calls.
    """
    cleaned_messages = []
    for msg in messages:
        if not isinstance(msg, dict):
            cleaned_messages.append(msg)
            continue
        
        # Create a copy without internal properties
        cleaned_msg = {k: v for k, v in msg.items() if k not in _INTERNAL_MESSAGE_PROPERTIES}
        cleaned_messages.append(cleaned_msg)
    
    return cleaned_messages

def _has_image_content(messages: List[Dict[str, Any]]) -> bool:
    """Check if messages contain image content."""
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        
        content = msg.get("content", "")
        
        # Check for OpenAI-style image content (list with image_url)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "image_url" or "image_url" in item:
                        return True
        
        # Check for Anthropic-style image content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image":
                    return True
        
        # Check for base64 image data in string content
        if isinstance(content, str):
            if "data:image" in content or "base64" in content.lower():
                return True
    
    return False

async def make_llm_api_call(
    messages: List[Dict[str, Any]],
    model_name: str,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = True,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    stop: Optional[List[str]] = None,
) -> Union[Dict[str, Any], AsyncGenerator, ModelResponse]:
    """
    Make an API call to a language model using LiteLLM.
    
    Args:
        messages: List of message dictionaries
        model_name: Name of the model to use (or "mock-ai" for testing)
        response_format: Optional response format specification
        temperature: Temperature for sampling (0-1)
        max_tokens: Maximum tokens to generate
        tools: Optional list of tool definitions
        tool_choice: Tool choice strategy ("auto", "required", "none")
        api_key: Optional API key override
        api_base: Optional API base URL override
        stream: Whether to stream the response
        top_p: Optional top_p for sampling
        model_id: Optional model ID for tracking
        headers: Optional headers to send with request
        extra_headers: Optional extra headers to send with request
        stop: Optional list of stop sequences
    """
    # Strip internal properties (like message_id) that some providers reject
    messages = _strip_internal_properties(messages)
    
    logger.info(f"LLM API call: {model_name} ({len(messages)} messages)")
    # Handle mock AI for stress testing
    if model_name == "mock-ai":
        logger.info(f"🎭 Using mock LLM provider for testing")
        from core.test_harness.mock_llm import get_mock_provider
        mock_provider = get_mock_provider(delay_ms=20)
        # Return generator directly (don't await it!)
        return mock_provider.acompletion(
            messages=messages,
            model=model_name,
            stream=stream,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    logger.info(f"Making LLM API call to model: {model_name} with {len(messages)} messages")
    
    from core.utils.config import config
    
    # SIMPLIFIED APPROACH: Always use custom endpoint directly, bypass router complexity
    if not config.OPENAI_COMPATIBLE_API_BASE:
        raise LLMError("OPENAI_COMPATIBLE_API_BASE must be configured to use local LLM server")
    
    # Actual model ID from your server (as returned by /v1/models endpoint)
    actual_model_id = "/home/nyra/Desktop/models/Qwen3-Omni-30B-A3B-Instruct"
    
    # Set API key in environment (LiteLLM requires it)
    api_key_value = config.OPENAI_COMPATIBLE_API_KEY if config.OPENAI_COMPATIBLE_API_KEY else "not-required"
    os.environ["OPENAI_API_KEY"] = api_key_value
    
    # CRITICAL: For OpenAI-compatible endpoints with api_base, LiteLLM needs:
    # - Provider prefix: "openai/" (tells LiteLLM to use OpenAI client)
    # - Model ID: What your server expects (will be sent after stripping "openai/")
    # When api_base is set, LiteLLM sends the model ID (after "openai/") directly to your server
    # So "openai//home/..." becomes "/home/..." when sent to server
    # LiteLLM handles the double slash correctly - it strips "openai/" and sends the rest
    litellm_model_name = f"openai{actual_model_id}"  # Result: "openai/home/nyra/Desktop/models/..."
    
    # Build params directly - bypass router entirely
    params = {
        "model": litellm_model_name,  # Use openai/ prefix for LiteLLM
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
        "api_base": config.OPENAI_COMPATIBLE_API_BASE,
        "api_key": api_key_value,
    }
    
    # Add optional params
    if response_format is not None:
        params["response_format"] = response_format
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    if top_p is not None:
        params["top_p"] = top_p
    if stop is not None:
        params["stop"] = stop
    if headers is not None:
        params["headers"] = headers
    if extra_headers is not None:
        params["extra_headers"] = extra_headers
    if tools is not None:
        params["tools"] = tools
        params["tool_choice"] = tool_choice
    if model_id is not None:
        params["model_id"] = model_id
    if stream:
        params["stream_options"] = {"include_usage": True}
    
    logger.warning(f"🚨 BYPASSING ROUTER: Calling LiteLLM directly with model={litellm_model_name}, api_base={config.OPENAI_COMPATIBLE_API_BASE}")
    
    try:
        _save_debug_input(params)
        # CRITICAL: Call LiteLLM directly with explicit api_base and api_key
        # LiteLLM requires provider prefix: use "openai/<model-id>" format
        # The api_base tells LiteLLM where to send the request
        # LiteLLM will send the actual model ID (after "openai/") to your server
        response = await litellm.acompletion(
            model=litellm_model_name,  # Format: openai/<actual-model-id>
            messages=messages,
            temperature=temperature,
            stream=stream,
            api_base=config.OPENAI_COMPATIBLE_API_BASE,
            api_key=api_key_value,
            max_tokens=max_tokens if max_tokens else None,
            top_p=top_p if top_p else None,
            stop=stop if stop else None,
            response_format=response_format if response_format else None,
            tools=tools if tools else None,
            tool_choice=tool_choice if tools else None,
            model_id=model_id if model_id else None,
            headers=headers if headers else None,
            extra_headers=extra_headers if extra_headers else None,
        )
        
        if stream and hasattr(response, '__aiter__'):
            return _wrap_streaming_response(response)
        return response
    except Exception as e:
        processed_error = ErrorProcessor.process_llm_error(e, context={"model": model_name})
        ErrorProcessor.log_error(processed_error)
        raise LLMError(processed_error.message)

async def _wrap_streaming_response(response) -> AsyncGenerator:
    """Wrap streaming response to handle errors during iteration."""
    try:
        async for chunk in response:
            yield chunk
    except Exception as e:
        # Convert streaming errors to processed errors
        processed_error = ErrorProcessor.process_llm_error(e)
        ErrorProcessor.log_error(processed_error)
        raise LLMError(processed_error.message)

setup_api_keys()
# Don't initialize router - we're bypassing it completely
# setup_provider_router()


if __name__ == "__main__":
    from litellm import completion
    import os

    setup_api_keys()

    response = completion(
        model="bedrock/anthropic.claude-sonnet-4-20250115-v1:0",
        messages=[{"role": "user", "content": "Hello! Testing 1M context window."}],
        max_tokens=100,
        extra_headers={
            "anthropic-beta": "context-1m-2025-08-07"  # 👈 Enable 1M context
        }
    )
