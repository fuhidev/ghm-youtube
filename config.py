"""
Configuration file for YouTube Tool.
This file stores API keys and other configuration settings.

IMPORTANT: Do not commit this file to version control with actual keys.
"""

# API Keys
DEEPSEEK_API_KEY = (
    "sk-b24c10868fa54902b565be1001666bfe"  # Replace with your actual API key
)
LEONARDO_API_KEY = (
    "2486143c-9dcb-48f5-8044-5be51de198fe"  # Replace with your actual API key
)

# Other configuration settings
DEFAULT_OUTPUT_DIR = "output"
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Leonardo.ai settings
LEONARDO_MODEL_ID = "ac614f96-1082-45bf-be9d-757f2d31c174"  # Leonardo Diffusion XL
LEONARDO_IMAGE_WIDTH = 1920
LEONARDO_IMAGE_HEIGHT = 1080

# DeepSeek settings
DEEPSEEK_MAX_TOKENS = 4000
DEEPSEEK_TEMPERATURE = 0.1
