# modules/translate.py
# Translation module using DeepSeek API
import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeepseekTranslator:
    """Class to handle translation from Chinese to Vietnamese using Deepseek API"""

    def __init__(self, api_key):
        """Initialize the translator with the API key"""
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def translate(
        self, text, source_lang="Chinese", target_lang="Vietnamese", retries=3, delay=2
    ):
        """
        Translate text from source language to target language

        Args:
            text (str): The text to translate
            source_lang (str): The source language (default: Chinese)
            target_lang (str): The target language (default: Vietnamese)
            retries (int): Number of retries if the API call fails
            delay (int): Delay between retries in seconds

        Returns:
            str: The translated text
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for translation")
            return ""

        # Prepare the prompt for translation
        prompt = f"Translate the following {source_lang} text to {target_lang}. Return only the translated text without any explanation or additional comments:\n\n{text}"

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Lower temperature for more consistent translations
            "max_tokens": 4000,
        }

        # Try to make the request with retries
        for attempt in range(retries):
            try:
                logger.info(
                    f"Sending translation request to Deepseek API (attempt {attempt+1}/{retries})"
                )
                response = requests.post(
                    self.api_url, headers=self.headers, data=json.dumps(payload)
                )

                if response.status_code == 200:
                    response_data = response.json()
                    translated_text = response_data["choices"][0]["message"][
                        "content"
                    ].strip()
                    logger.info(
                        f"Translation successful ({len(text)} chars -> {len(translated_text)} chars)"
                    )
                    return translated_text
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    if attempt < retries - 1:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
            except Exception as e:
                logger.error(f"Error during translation: {str(e)}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # If all retries failed
        logger.error("All translation attempts failed")
        raise Exception("Failed to translate text using Deepseek API")


def translate_chinese_to_vietnamese(text, api_key):
    """
    Convenience function to translate Chinese text to Vietnamese

    Args:
        text (str): The Chinese text to translate
        api_key (str): Deepseek API key

    Returns:
        str: The translated Vietnamese text
    """
    translator = DeepseekTranslator(api_key)
    return translator.translate(text)


# For testing the module
if __name__ == "__main__":
    # Example usage
    test_text = "你好，世界！这是一个测试。"
    api_key = "your-api-key-here"  # Replace with actual API key when testing

    try:
        translator = DeepseekTranslator(api_key)
        translated = translator.translate(test_text)
        print(f"Original: {test_text}")
        print(f"Translated: {translated}")
    except Exception as e:
        print(f"Error: {e}")
