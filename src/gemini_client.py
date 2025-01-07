from dataclasses import dataclass
from typing import Optional, Dict
import google.generativeai as genai
import json
import logging
from .config import GEMINI_CONFIG, ErrorCodes

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RecognitionResult:
    success: bool
    statement_type: Optional[str] = None
    confidence: Optional[float] = None
    extracted_data: Optional[Dict] = None
    error: Optional[str] = None

class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=GEMINI_CONFIG["model"])

    def analyze_document(self, file_obj, mime_type: str) -> RecognitionResult:
        """Analyze financial statements using Gemini Vision API"""
        try:
            if not file_obj:
                logger.error("No file provided")
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.RECOGNITION_FAILED}: No file provided"
                )

            logger.info("\n=== Document Analysis ===")
            
            # Upload file to Gemini
            try:
                file = genai.upload_file(file_obj, mime_type=mime_type)
                logger.info(f"Uploaded file: {file.name}")

                # Add the system prompt
                system_prompt = """Analyze this financial statement and extract all data into structured JSON.

Key Requirements:
1. Structure:
{
    "metadata": {
        "currency": "GBP",
        "scale": "millions",
        "unit_symbol": "£m"
    },
    "statements": {
        "profit_and_loss": {
            "2023": {...},
            "2022": {...}
        },
        "balance_sheet": {
            "2023": {...},
            "2022": {...}
        }
    }
}

2. Data Rules:
- First identify which pages contain which statements
- Extract EVERY line item exactly as shown
- Convert all values to numbers at the scale shown
- Use negative numbers for expenses/liabilities
- Remove currency symbols from values but capture in metadata
- Round to 3 decimal places
- Maintain exact ordering from statements

Respond ONLY with the JSON object."""

                # Make API call
                response = self.model.generate_content(
                    [system_prompt, file],
                    generation_config={
                        "temperature": 0.1,
                        "candidate_count": 1,
                        "max_output_tokens": 2048
                    }
                )

                # Process response
                if not response or not response.text:
                    logger.error("Empty response from API")
                    return RecognitionResult(
                        success=False,
                        error=f"{ErrorCodes.RECOGNITION_FAILED}: Empty response from API"
                    )

                try:
                    content = response.text.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1]
                    if content.endswith("```"):
                        content = content.rsplit("```", 1)[0]
                        
                    parsed_data = json.loads(content)
                    logger.info("Successfully parsed JSON response")
                    
                    return RecognitionResult(
                        success=True,
                        statement_type="Multiple",
                        confidence=1.0,
                        extracted_data=parsed_data
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {str(e)}")
                    return RecognitionResult(
                        success=False,
                        error=f"{ErrorCodes.RECOGNITION_FAILED}: Invalid JSON response"
                    )

            finally:
                # Clean up uploaded file
                if 'file' in locals():
                    try:
                        genai.delete_file(file.name)
                        logger.info(f"Deleted uploaded file: {file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete uploaded file {file.name}: {str(e)}")

        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.RECOGNITION_FAILED}: {str(e)}"
            ) 