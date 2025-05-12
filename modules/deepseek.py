# modules/deepseek.py
# Module for interacting with the DeepSeek AI API
import requests
import json
import time
import logging
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import DEEPSEEK_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeepSeek:
    """Class to handle interactions with DeepSeek API"""

    def __init__(self, api_key=None):
        """Initialize the DeepSeek client with API key"""
        # Priority: 1) Passed API key, 2) Environment variable, 3) Config file, 4) Default key
        self.api_key = (
            api_key
            or os.environ.get("DEEPSEEK_API_KEY")
            or CONFIG_API_KEY
            or "sk-b24c10868fa54902b565be1001666bfe"
        )

        # Print information about where the API key was sourced from
        if api_key:
            logger.info("Using provided API key")
        elif os.environ.get("DEEPSEEK_API_KEY"):
            logger.info("Using API key from environment variable")
        elif CONFIG_API_KEY:
            logger.info("Using API key from config.py")
        else:
            logger.warning("Using default API key - consider setting your own API key")

        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def chat(
        self,
        system_prompt,
        prompt,
        temperature=0.1,
        max_tokens=4000,
        retries=3,
        delay=2,
    ):
        """
        Send a chat request to DeepSeek API

        Args:
            prompt (str): The prompt to send
            temperature (float): Temperature parameter for generation
            max_tokens (int): Maximum number of tokens to generate
            retries (int): Number of retries if the API call fails
            delay (int): Delay between retries in seconds

        Returns:
            str: The response from the API
        """
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt provided for chat")
            return ""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Remove None values from the messages list
        payload["messages"] = [
            message for message in payload["messages"] if message is not None
        ]

        # Try to make the request with retries
        for attempt in range(retries):
            try:
                logger.info(
                    f"Sending chat request to Deepseek API (attempt {attempt+1}/{retries})"
                )
                response = requests.post(
                    self.api_url, headers=self.headers, data=json.dumps(payload)
                )

                if response.status_code == 200:
                    response_data = response.json()
                    result = response_data["choices"][0]["message"]["content"].strip()
                    logger.info(
                        f"Chat request successful (response length: {len(result)} chars)"
                    )
                    return result
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    if attempt < retries - 1:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
            except Exception as e:
                logger.error(f"Error during API call: {str(e)}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # If all retries failed
        logger.error("All chat attempts failed")
        raise Exception("Failed to get response from Deepseek API")


# For testing the module
if __name__ == "__main__":
    test_prompt = "What is the capital of Vietnam?"
    try:
        deepseek = DeepSeek()
        response = deepseek.chat(test_prompt)
        print(f"Prompt: {test_prompt}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
