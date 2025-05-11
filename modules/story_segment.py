# modules/story_segment.py
import re
import math
import json
import os
import logging
import requests
import time
from typing import List, Dict, Optional
import textwrap

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StorySegmenter:
    """
    Class to segment a story into sections and generate image prompts
    """

    def __init__(self, story_text: str, num_segments: int = 8):
        """
        Initialize the segmenter

        Args:
            story_text (str): The full text of the story
            num_segments (int): Number of segments to divide the story into
        """
        self.story_text = story_text
        self.num_segments = num_segments
        self.segments = []
        self.prompts = []

    def segment_by_paragraphs(self) -> List[str]:
        """
        Segment the story by paragraphs, trying to create equal-sized segments

        Returns:
            List[str]: List of segmented text portions
        """
        # Split by paragraphs (empty lines)
        paragraphs = re.split(r"\n\s*\n", self.story_text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if len(paragraphs) <= self.num_segments:
            # If we have fewer paragraphs than desired segments
            self.segments = paragraphs
            # Fill remaining segments with empty strings
            self.segments.extend([""] * (self.num_segments - len(paragraphs)))
        else:
            # Calculate how many paragraphs should go in each segment
            paragraphs_per_segment = math.ceil(len(paragraphs) / self.num_segments)

            # Group paragraphs into segments
            self.segments = []
            for i in range(0, len(paragraphs), paragraphs_per_segment):
                segment_paragraphs = paragraphs[i : i + paragraphs_per_segment]
                self.segments.append("\n\n".join(segment_paragraphs))

            # If we have more segments than needed, combine the last ones
            if len(self.segments) > self.num_segments:
                last_segments = self.segments[self.num_segments - 1 :]
                self.segments = self.segments[: self.num_segments - 1]
                self.segments.append("\n\n".join(last_segments))

        return self.segments

    def generate_prompts(self) -> List[str]:
        """
        Generate image prompts for each segment

        Returns:
            List[str]: List of image prompts
        """
        if not self.segments:
            self.segment_by_paragraphs()

        self.prompts = []

        for i, segment in enumerate(self.segments):
            if not segment:
                # Skip empty segments
                self.prompts.append("")
                continue

            # Extract the most descriptive parts from the segment
            # Remove dialog (text in quotes) as it's less useful for scene description
            clean_text = re.sub(r'"[^"]*"', "", segment)

            # Extract lines that describe scenes, objects, or characters
            descriptive_lines = []
            for line in clean_text.split("\n"):
                if any(
                    word in line.lower()
                    for word in [
                        "nhìn",
                        "mặc",
                        "ánh",
                        "màu",
                        "phát hiện",
                        "kinh ngạc",
                        "thấy",
                        "cảnh",
                        "hiện ra",
                    ]
                ):
                    descriptive_lines.append(line)

            # If we didn't find descriptive lines, use the first 2-3 sentences
            if not descriptive_lines:
                sentences = re.split(r"[.!?]\s+", clean_text)
                descriptive_lines = sentences[: min(3, len(sentences))]

            # Create a prompt with key elements
            prompt_text = " ".join(descriptive_lines)

            # Make the prompt concise (max 250 characters)
            prompt = textwrap.shorten(prompt_text, width=250, placeholder="...")

            # Add style instructions for consistency
            style_instruction = (
                "Hình ảnh hiện thực, phong cách tiên hiệp, "
                "fantasy, chi tiết cao, ánh sáng tự nhiên"
            )

            final_prompt = f"{prompt} {style_instruction}"
            self.prompts.append(final_prompt)

        return self.prompts

    def save_segments_and_prompts(self, output_dir: str) -> str:
        """
        Save segments and prompts to files

        Args:
            output_dir (str): Directory to save output files

        Returns:
            str: Path to the saved JSON file
        """
        os.makedirs(output_dir, exist_ok=True)

        if not self.segments:
            self.segment_by_paragraphs()

        if not self.prompts:
            self.generate_prompts()

        output = {"num_segments": self.num_segments, "segments": []}

        for i, (segment, prompt) in enumerate(zip(self.segments, self.prompts)):
            output["segments"].append(
                {"segment_id": i + 1, "text": segment, "prompt": prompt}
            )

        output_path = os.path.join(output_dir, "story_segments.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved segments and prompts to {output_path}")
        return output_path


class LeonardoImageGenerator:
    """
    Class to generate images using Leonardo.ai API
    """

    def __init__(self, api_key: str):
        """
        Initialize the image generator

        Args:
            api_key (str): Leonardo.ai API key
        """
        self.api_key = api_key
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Default model ID (you can change this based on what works best)
        self.model_id = "e316348f-7773-490e-adcd-46757c738eb7"  # Leonardo Diffusion XL

    def generate_image(self, prompt: str, negative_prompt: str = "") -> Optional[str]:
        """
        Generate an image using Leonardo.ai

        Args:
            prompt (str): The prompt for image generation
            negative_prompt (str): Negative prompt to avoid certain elements

        Returns:
            str: URL of the generated image, or None if failed
        """
        if not prompt:
            logger.warning("Empty prompt, skipping image generation")
            return None

        # Create generation
        generation_url = f"{self.base_url}/generations"
        payload = {
            "prompt": prompt,
            "modelId": self.model_id,
            "negative_prompt": negative_prompt
            or "blurry, distorted, deformed, text, bad anatomy, extra limbs",
            "width": 1024,
            "height": 768,
            "num_images": 1,
            "sd_version": "v2",  # Using Stable Diffusion v2
        }

        try:
            logger.info(f"Creating generation job for prompt: {prompt[:50]}...")
            response = requests.post(generation_url, json=payload, headers=self.headers)
            response.raise_for_status()

            generation_id = response.json()["sdGenerationJob"]["generationId"]
            logger.info(f"Generation job created with ID: {generation_id}")

            # Poll for generation results
            max_attempts = 20
            attempts = 0
            while attempts < max_attempts:
                attempts += 1

                logger.info(
                    f"Checking generation status (attempt {attempts}/{max_attempts})..."
                )
                status_url = f"{self.base_url}/generations/{generation_id}"
                status_response = requests.get(status_url, headers=self.headers)
                status_response.raise_for_status()

                status_data = status_response.json()
                status = status_data["sdGenerationJob"]["status"]

                if status == "COMPLETE":
                    image_url = status_data["generations_by_pk"]["generated_images"][0][
                        "url"
                    ]
                    logger.info(f"Image generated successfully: {image_url}")
                    return image_url
                elif status == "FAILED":
                    logger.error("Image generation failed")
                    return None

                logger.info(f"Generation status: {status}, waiting...")
                time.sleep(5)  # Wait 5 seconds before checking again

            logger.error("Exceeded maximum attempts waiting for image generation")
            return None

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None

    def download_image(self, image_url: str, output_path: str) -> bool:
        """
        Download an image from a URL

        Args:
            image_url (str): URL of the image to download
            output_path (str): Path to save the downloaded image

        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Image downloaded successfully to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return False


def process_story_for_images(
    story_text: str, num_images: int, output_dir: str, api_key: str
) -> List[str]:
    """
    Process a story to generate images for each segment

    Args:
        story_text (str): The story text
        num_images (int): Number of images to generate
        output_dir (str): Directory to save output files
        api_key (str): Leonardo.ai API key

    Returns:
        List[str]: Paths to generated images
    """
    # Create segments and prompts
    segmenter = StorySegmenter(story_text, num_images)
    segments = segmenter.segment_by_paragraphs()
    prompts = segmenter.generate_prompts()
    segmenter.save_segments_and_prompts(output_dir)

    # Generate images
    image_generator = LeonardoImageGenerator(api_key)
    image_paths = []

    for i, prompt in enumerate(prompts):
        if not prompt:
            # Skip empty prompts
            logger.warning(f"Skipping segment {i+1} due to empty prompt")
            image_paths.append("")
            continue

        logger.info(f"Generating image for segment {i+1}/{num_images}")
        image_url = image_generator.generate_image(prompt)

        if image_url:
            # Download the image
            image_path = os.path.join(output_dir, f"image_{i+1:02d}.png")
            success = image_generator.download_image(image_url, image_path)

            if success:
                image_paths.append(image_path)
            else:
                image_paths.append("")
        else:
            image_paths.append("")

    return image_paths


if __name__ == "__main__":
    # Example usage
    sample_story = """
    Ý thức của Vân Triệt dần tỉnh lại.

    Chuyện gì đây... Chẳng lẽ ta vẫn chưa chết? Rõ ràng ta đã rơi xuống Tuyệt Vân Nhai, sao có thể còn sống được!
    """

    segmenter = StorySegmenter(sample_story, 3)
    segments = segmenter.segment_by_paragraphs()
    prompts = segmenter.generate_prompts()

    for i, (segment, prompt) in enumerate(zip(segments, prompts)):
        print(f"Segment {i+1}:")
        print(segment[:100] + "..." if len(segment) > 100 else segment)
        print(f"Prompt: {prompt}")
        print("-" * 50)
