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

            analysis_model = genai.GenerativeModel(model_name=GEMINI_CONFIG["analysis_model"])
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
        "currency": "DETECT FROM DOCUMENT (e.g. GBP, USD, EUR, etc.)",
        "scale": "DETECT FROM DOCUMENT (e.g., millions, thousands, billions)",
        "unit_symbol": "DETECT FROM DOCUMENT (e.g., $m, £k, €B)"
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
4. Use spaces in line item names, not underscores
5. Use negative numbers for liabilities/creditors
6. Capitalize the first letter of each word in line item names
7. Follow ONLY this nesting hierarchy:
   metadata -> flat key/values
   statements -> profit_and_loss/balance_sheet -> years -> flat key/values
8. No other nested objects allowed
9. Output valid JSON only"""

                # Make API call
                try:
                    response = analysis_model.generate_content(
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

            # First consolidate profit and loss statements
            profit_loss_result = self._consolidate_statement_type("profit_and_loss")
            if not profit_loss_result.success:
                return profit_loss_result

            # Then consolidate balance sheet statements
            balance_sheet_result = self._consolidate_statement_type("balance_sheet")
            if not balance_sheet_result.success:
                return balance_sheet_result

            # Combine the results
            consolidated_data = {
                "metadata": self.extracted_jsons[0]["metadata"],  # Use metadata from first statement
                "statements": {
                    "profit_and_loss": profit_loss_result.extracted_data,
                    "balance_sheet": balance_sheet_result.extracted_data
                }
            }

            return RecognitionResult(
                success=True,
                statement_type="Consolidated",
                confidence=1.0,
                extracted_data=consolidated_data
            )

        except Exception as e:
            logger.error(f"Consolidation failed: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.CONSOLIDATION_FAILED}: {str(e)}"
            )

    def _consolidate_statement_type(self, statement_type: str) -> RecognitionResult:
        """Consolidate a specific type of statement (profit_and_loss or balance_sheet)"""
        try:
            consolidation_model = genai.GenerativeModel(GEMINI_CONFIG["consolidation_model"])
            
            # Extract all data for this statement type
            statement_data = []
            for json_obj in self.extracted_jsons:
                if statement_type in json_obj.get("statements", {}):
                    statement_data.append(json_obj["statements"][statement_type])

            if not statement_data:
                logger.info(f"No {statement_type} statements to consolidate")
                return RecognitionResult(
                    success=True,
                    statement_type=statement_type,
                    extracted_data={}
                )

            # Format the prompt for this statement type
            prompt = {
                "role": "user",
                "parts": [{
                    "text": f"""Consolidate these {statement_type} statements into a single JSON object.

Rules for combining line items:
1. Normalize names by:
   - Removing underscores, arrows (→), and spaces
   - Ignoring case differences
   - Example: "Fixed_Assets → Intangible_assets" = "FixedAssetsIntangibleAssets"
2. When multiple items match after normalization, combine their values
3. Use the most common name format from the input data
4. Preserve all unique line items

Input statements:
{json.dumps(statement_data, indent=2)}"""
                }]
            }

            # Make API call
            response = consolidation_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "candidate_count": 1,
                    "max_output_tokens": 8192
                }
            )

            if not response or not response.text:
                raise ValueError(f"Empty response from API for {statement_type}")

            # Add debug logging for the raw response
            debug_dir = 'debug'
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, f"consolidation_{statement_type}_response.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"[DEBUG] Raw consolidation response saved to: {debug_file}")

            # Clean and parse the response
            cleaned_response = response.text.strip()
            cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
            start = cleaned_response.find('{')
            end = cleaned_response.rfind('}') + 1
            
            if start >= 0 and end > 0:
                cleaned_response = cleaned_response[start:end]
                try:
                    consolidated_data = json.loads(cleaned_response)
                    logger.info(f"[SUCCESS] Successfully consolidated {statement_type}")
                    return RecognitionResult(
                        success=True,
                        statement_type=statement_type,
                        extracted_data=consolidated_data
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"[ERROR] Invalid JSON in consolidation response. See: {debug_file}")
                    logger.error(f"Error details: {str(e)}")
                    logger.error("\nFirst 500 characters of cleaned response:")
                    logger.error(f"{cleaned_response[:500]}...")
                    return RecognitionResult(
                        success=False,
                        error=f"{ErrorCodes.CONSOLIDATION_FAILED}: Invalid JSON in consolidation response for {statement_type}. Debug file: {debug_file}"
                    )
            else:
                raise ValueError(f"No valid JSON found in response for {statement_type}")

        except Exception as e:
            logger.error(f"Failed to consolidate {statement_type}: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.CONSOLIDATION_FAILED}: Failed to consolidate {statement_type}: {str(e)}"
            ) 