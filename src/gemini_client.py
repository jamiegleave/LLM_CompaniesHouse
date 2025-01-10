from dataclasses import dataclass
from typing import Optional, Dict
import google.generativeai as genai
import json
import logging
from .config import GEMINI_CONFIG, ErrorCodes
import os

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
        self.extracted_jsons = []

    def analyze_document(self, file_obj, mime_type: str) -> RecognitionResult:
        """Analyze single financial statement using Gemini Vision API"""
        try:
            if not file_obj:
                logger.error("No file provided")
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.RECOGNITION_FAILED}: No file provided"
                )

            logger.info(f"\n{'='*50}")
            logger.info(f"Processing: {file_obj.name}")
            logger.info(f"{'='*50}")
            
            # Upload file to Gemini
            try:
                file = genai.upload_file(file_obj, mime_type=mime_type)
                logger.info("[SUCCESS] File uploaded successfully")

                # Updated system prompt with stricter response format and structure
                system_prompt = """You are a financial data parser that outputs valid JSON. Extract ALL financial data visible in the document.

STRUCTURE:
{
    "metadata": {
        "currency": "GBP",
        "scale": "millions",
        "unit_symbol": "£m"
    },
    "statements": {
        "profit_and_loss": {
            // Each year should be a separate object here with flat structure
            // Extract all line items from the document
        },
        "balance_sheet": {
            // Each year should be a separate object here with flat structure
            // Extract all line items from the document
        }
    }
}

CRITICAL RULES:
1. Extract ALL visible financial data from the document
2. Group data by statement type, then by year
3. Use decimal numbers (e.g., 50.0 not 50)
4. Use spaces in names, not underscores
5. Use negative numbers for liabilities/creditors
6. Follow ONLY this nesting hierarchy:
   metadata -> flat key/values
   statements -> profit_and_loss/balance_sheet -> years -> flat key/values
7. No other nested objects allowed
8. Output valid JSON only"""

                # Make API call
                try:
                    response = self.model.generate_content(
                        [system_prompt, file],
                        generation_config={
                            "temperature": 0.1,
                            "candidate_count": 1,
                            "max_output_tokens": 4096
                        }
                    )

                    if not response or not response.text:
                        logger.error("[ERROR] Empty response from API - possible quota exceeded")
                        return RecognitionResult(
                            success=False,
                            error=f"{ErrorCodes.API_QUOTA_EXCEEDED}: No response from API - quota may be exceeded"
                        )

                    # Save raw response for debugging
                    raw_response = response.text.strip()
                    debug_dir = 'debug'
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    debug_file = os.path.join(debug_dir, f"{file_obj.name.replace('.pdf', '')}_raw_response.txt")
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(raw_response)
                    logger.info(f"[DEBUG] Raw API response saved to: {debug_file}")

                    # Parse JSON response
                    try:
                        # Try to find JSON content if wrapped in markdown
                        if raw_response.startswith('```'):
                            start = raw_response.find('{')
                            end = raw_response.rfind('}') + 1
                            if start != -1 and end != 0:
                                raw_response = raw_response[start:end]

                        parsed_data = json.loads(raw_response)
                        logger.info("[SUCCESS] Successfully parsed JSON response")
                        
                        # Store the extracted JSON for later consolidation
                        if parsed_data:
                            self.extracted_jsons.append(parsed_data)
                            logger.info(f"[SUCCESS] Added to consolidation queue (Total: {len(self.extracted_jsons)})")
                        
                        return RecognitionResult(
                            success=True,
                            statement_type="Multiple",
                            confidence=1.0,
                            extracted_data=parsed_data
                        )

                    except json.JSONDecodeError as e:
                        logger.error(f"[ERROR] Invalid JSON from LLM. See: {debug_file}")
                        logger.error(f"Error details: {str(e)}")
                        logger.error("\nFirst 500 characters of response:")
                        logger.error(f"{raw_response[:500]}...")
                        return RecognitionResult(
                            success=False,
                            error=f"{ErrorCodes.RECOGNITION_FAILED}: Invalid JSON response. Debug file: {debug_file}"
                        )

                except Exception as e:
                    if "quota" in str(e).lower():
                        logger.error(f"[ERROR] API quota exceeded: {str(e)}")
                        return RecognitionResult(
                            success=False,
                            error=f"{ErrorCodes.API_QUOTA_EXCEEDED}: {str(e)}"
                        )
                    else:
                        logger.error(f"[ERROR] API call failed: {str(e)}")
                        return RecognitionResult(
                            success=False,
                            error=f"{ErrorCodes.API_ERROR}: {str(e)}"
                        )

            finally:
                if 'file' in locals():
                    try:
                        genai.delete_file(file.name)
                        logger.info("[SUCCESS] Cleaned up uploaded file")
                    except Exception as e:
                        logger.warning(f"[WARNING] Failed to delete uploaded file: {str(e)}")

        except Exception as e:
            logger.error(f"\n=== Processing Error ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.RECOGNITION_FAILED}: {str(e)}"
            ) 

    def consolidate_statements(self) -> RecognitionResult:
        """Consolidate all extracted statements into a single JSON"""
        try:
            if not self.extracted_jsons:
                logger.info("No statements to consolidate")
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.CONSOLIDATION_FAILED}: No statements to consolidate"
                )

            consolidation_prompt = """You are a financial data consolidator. Your task is to combine ALL provided statements into a single JSON.

INPUT STATEMENTS:
{}

CRITICAL RULES:
1. PRESERVE ALL YEARS from input statements - do not create or remove any years
2. Use ONLY data from the input statements - never generate example data
3. Include ALL years found in ANY input statement
4. Format numbers consistently:
   - Convert strings to numbers
   - Remove commas
   - Convert parentheses to negatives
5. Use spaces in names, not underscores
6. Flatten any nested structures
7. Follow only this hierarchy:
   metadata -> flat key/values
   statements -> profit_and_loss/balance_sheet -> years -> flat key/values

EXAMPLE: If inputs contain 2018, 2019, 2020, and 2021 data, the output must include ALL those years with their actual values."""

            # Convert input JSONs to formatted string
            input_data = "\n\n".join(f"Statement {i+1}:\n{json.dumps(json_obj, indent=2)}" 
                                   for i, json_obj in enumerate(self.extracted_jsons))
            
            # Format the complete prompt with input data
            complete_prompt = consolidation_prompt.format(input_data)

            response = self.model.generate_content(
                complete_prompt,
                generation_config={
                    "temperature": 0.1,
                    "candidate_count": 1,
                    "max_output_tokens": 8192
                }
            )

            if not response or not response.text:
                raise ValueError("Empty response from API")

            # Save raw response to file
            try:
                with open('debug/raw_response.txt', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info("[DEBUG] Saved raw response to debug/raw_response.txt")
            except Exception as e:
                logger.error(f"[WARNING] Could not save raw response: {str(e)}")

            # Parse consolidated JSON
            try:
                content = response.text.strip()
                logger.debug(f"Raw content length: {len(content)} characters")
                
                # Find the first { and last } to extract just the JSON object
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON object found in response")
                
                content = content[start_idx:end_idx]
                
                # Validate JSON structure (count braces)
                open_braces = content.count('{')
                close_braces = content.count('}')
                
                if open_braces != close_braces:
                    logger.warning(f"Mismatched braces: {open_braces} opening vs {close_braces} closing")
                    # Find the last balanced position
                    count = 0
                    last_balanced_pos = 0
                    for i, char in enumerate(content):
                        if char == '{':
                            count += 1
                        elif char == '}':
                            count -= 1
                        if count == 0:
                            last_balanced_pos = i + 1
                    content = content[:last_balanced_pos]
                
                logger.debug(f"Cleaned content length: {len(content)} characters")
                
                # Save cleaned content to file
                try:
                    with open('debug/cleaned_response.json', 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info("[DEBUG] Saved cleaned response to debug/cleaned_response.json")
                except Exception as e:
                    logger.error(f"[WARNING] Could not save cleaned response: {str(e)}")
                
                # Validate JSON before parsing
                try:
                    consolidated_data = json.loads(content)
                    logger.info("[SUCCESS] Successfully parsed consolidated JSON")
                    return RecognitionResult(
                        success=True,
                        statement_type="Consolidated",
                        confidence=1.0,
                        extracted_data=consolidated_data
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"[ERROR] JSON validation failed: {str(e)}")
                    raise

            except json.JSONDecodeError as e:
                logger.error("\n=== JSON Parsing Error ===")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error message: {str(e)}")
                logger.error(f"Error position: {e.pos}")
                logger.error("\nContent snippet around error:")
                start = max(0, e.pos - 50)
                end = min(len(content), e.pos + 50)
                logger.error(f"...{content[start:e.pos]} >>> ERROR HERE <<< {content[e.pos:end]}...")
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.INVALID_JSON}: Failed to parse consolidated JSON: {str(e)}"
                )

        except Exception as e:
            logger.error(f"Consolidation failed: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.CONSOLIDATION_FAILED}: {str(e)}"
            ) 