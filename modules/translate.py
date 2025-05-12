# modules/translate.py
# Translation module using DeepSeek API
import requests
import json
import time
import logging
import os
from modules.deepseek import DeepSeek

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeepseekTranslator:
    """Class to handle translation using Deepseek API"""

    def __init__(self, api_key=None):
        """Initialize the translator with a DeepSeek instance"""
        self.deepseek = DeepSeek(api_key)

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

        # Use the DeepSeek chat method
        return self.deepseek.chat(
            prompt, temperature=0.1, max_tokens=4000, retries=retries, delay=delay
        )

    def translate_long_text(
        self,
        text,
        source_lang="Chinese",
        target_lang="Vietnamese",
        chunk_size=1500,
        retries=3,
        delay=2,
    ):
        """
        Translate long text by breaking it into manageable chunks

        Args:
            text (str): The long text to translate
            source_lang (str): Source language
            target_lang (str): Target language
            chunk_size (int): Approximate size of each chunk in characters
            retries (int): Number of retries for API calls
            delay (int): Delay between retries

        Returns:
            str: Complete translated text
        """
        if not text or not text.strip():
            return ""

        # If text is short enough, translate it directly
        if len(text) <= chunk_size:
            return self.translate(text, source_lang, target_lang, retries, delay)

        logger.info(
            f"Text length ({len(text)} chars) exceeds chunk size. Breaking into chunks."
        )

        # Split text into paragraphs
        paragraphs = text.split("\n")
        chunks = []
        current_chunk = []
        current_length = 0

        # Group paragraphs into chunks of appropriate size
        for para in paragraphs:
            if current_length + len(para) > chunk_size and current_chunk:
                # If adding this paragraph exceeds chunk size, save current chunk
                chunks.append("\n".join(current_chunk))
                current_chunk = [para]
                current_length = len(para)
            else:
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_length += len(para)

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        # Translate each chunk
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            translated_chunk = self.translate(
                chunk, source_lang, target_lang, retries, delay
            )
            translated_chunks.append(translated_chunk)

            # Add delay between chunk translations to avoid rate limiting
            if i < len(chunks) - 1:
                time.sleep(delay)

        # Join the translated chunks
        return "\n".join(translated_chunks)


def translate_chinese_to_vietnamese(text, api_key=None):
    """
    Convenience function to translate Chinese text to Vietnamese

    Args:
        text (str): The Chinese text to translate
        api_key (str, optional): Deepseek API key

    Returns:
        str: The translated Vietnamese text
    """
    translator = DeepseekTranslator(api_key)
    return translator.translate_long_text(text)


# For testing the module
if __name__ == "__main__":
    # Example usage
    test_text = "你好，世界！这是一个测试。"

    try:
        translator = DeepseekTranslator()
        translated = translator.translate(test_text)
        print(f"Original: {test_text}")
        print(f"Translated: {translated}")
    except Exception as e:
        print(f"Error: {e}")
