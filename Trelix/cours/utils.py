import re
import html
import json
import google.generativeai as genai
from django.conf import settings
from typing import List, Dict, Any


class GeminiFlashcardGenerator:
    
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or getattr(settings, 'GOOGLE_API_KEY', None)
        if not self.api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in settings or .env file.")
        
        genai.configure(api_key=self.api_key)
        
        # Determine model name from explicit argument, environment, or default
        configured_model = (
            model_name
            or getattr(settings, 'GEMINI_MODEL_NAME', None)
            or 'models/gemini-2.5-flash-lite'
        )

        # Normalize for SDK: strip optional 'models/' prefix
        normalized_model = configured_model.replace('models/', '', 1) if configured_model.startswith('models/') else configured_model

        try:
            self.model = genai.GenerativeModel(normalized_model)
        except Exception as e:
            raise ValueError(
                f"Failed to initialize Gemini model. Configured='{configured_model}', used='{normalized_model}'. Error: {str(e)}"
            )
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Trim and return
        return text.strip()
    
    @staticmethod
    def structure_course_content(course, chapters) -> str:
        sections = []
        
        # Course overview
        sections.append("=== COURSE OVERVIEW ===")
        sections.append(f"Title: {GeminiFlashcardGenerator.sanitize_text(course.title)}")
        sections.append(f"Level: {course.level.title()}")
        if course.description:
            sections.append(f"Description: {GeminiFlashcardGenerator.sanitize_text(course.description)}")
        sections.append("")
        
        # Chapter content
        sections.append("=== CHAPTERS ===")
        for idx, chapter in enumerate(chapters.order_by('order'), 1):
            sections.append(f"Chapter {idx}: {GeminiFlashcardGenerator.sanitize_text(chapter.title)}")
            if chapter.description:
                content = GeminiFlashcardGenerator.sanitize_text(chapter.description)
                sections.append(f"Content: {content}")
            sections.append("")
        
        return "\n".join(sections)
    
    def generate_flashcards(self, course_content: str, num_cards: int = 10) -> List[Dict[str, Any]]:
        prompt = f"""You are an educational assistant. Based on the following course content, create {num_cards} high-quality flashcards.

COURSE CONTENT:
{course_content}

INSTRUCTIONS:
1. Create exactly {num_cards} flashcards covering key concepts, definitions, and important information
2. Each flashcard should have:
   - A clear, concise question or term on the FRONT
   - A detailed, accurate answer on the BACK
3. Focus on important concepts that students need to remember
4. Make questions thought-provoking but answerable from the content
5. Ensure answers are comprehensive but concise

OUTPUT FORMAT (strict JSON array):
[
  {{
    "front": "Question or term here",
    "back": "Answer or definition here"
  }},
  ...
]

IMPORTANT: Return ONLY valid JSON array. No markdown, no code blocks, no explanations. Just the JSON array."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            
            # Extract text from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON
            flashcards = json.loads(response_text)
            
            # Validate structure
            if not isinstance(flashcards, list):
                raise ValueError("Response is not a list")
            
            # Ensure all cards have front and back
            validated_cards = []
            for card in flashcards:
                if isinstance(card, dict) and 'front' in card and 'back' in card:
                    validated_cards.append({
                        'front': str(card['front']).strip(),
                        'back': str(card['back']).strip()
                    })
            
            if not validated_cards:
                raise ValueError("No valid flashcards found in response")
            
            return validated_cards
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response from Gemini API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating flashcards: {str(e)}")


def get_course_content_for_flashcards(course) -> str:
    chapters = course.chapters.all()
    return GeminiFlashcardGenerator.structure_course_content(course, chapters)

