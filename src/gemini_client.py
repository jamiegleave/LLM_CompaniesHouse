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

                    # Parse JSON response
                    try:
                        # Try to find JSON content if wrapped in markdown
                        raw_response = response.text.strip()
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
                        logger.error(f"[ERROR] Invalid JSON from LLM")
                        logger.error(f"Error details: {str(e)}")
                        logger.error("\nFirst 500 characters of response:")
                        logger.error(f"{raw_response[:500]}...")
                        return RecognitionResult(
                            success=False,
                            error=f"{ErrorCodes.RECOGNITION_FAILED}: Invalid JSON response"
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
            # Get standardized line item names first
            standardized_names = self._get_standardized_line_items(statement_type)
            
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

            # Chunk the statements into groups of 5 years
            consolidated_chunks = {}
            chunk_size = 5
            years = sorted(list({year for stmt in statement_data for year in stmt.keys()}))
            
            for i in range(0, len(years), chunk_size):
                chunk_years = years[i:i + chunk_size]
                chunk_data = []
                
                # Create subset of data for each chunk
                for stmt in statement_data:
                    chunk_stmt = {year: stmt[year] for year in chunk_years if year in stmt}
                    if chunk_stmt:
                        chunk_data.append(chunk_stmt)

                # Format the prompt for this chunk
                prompt = {
                    "role": "user",
                    "parts": [{
                        "text": f"""Consolidate these {statement_type} statements for years {chunk_years[0]}-{chunk_years[-1]} into a single JSON object.

Rules for combining line items:
1. Use these standardized names for line items:
{json.dumps(standardized_names, indent=2)}
2. When multiple items map to the same standardized name, combine their values
3. Preserve all unique line items
4. Use the standardized name format in the output

Input statements:
{json.dumps(chunk_data, indent=2)}"""
                    }]
                }

                # Process chunk
                response = consolidation_model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
                        "candidate_count": 1,
                        "max_output_tokens": 8192
                    }
                )

                if not response or not response.text:
                    raise ValueError(f"Empty response from API for {statement_type} chunk {chunk_years}")

                # Clean and parse the response
                cleaned_response = response.text.strip()
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
                start = cleaned_response.find('{')
                end = cleaned_response.rfind('}') + 1
                
                if start >= 0 and end > 0:
                    cleaned_response = cleaned_response[start:end]
                    chunk_result = json.loads(cleaned_response)
                    consolidated_chunks.update(chunk_result)
                else:
                    raise ValueError(f"No valid JSON found in response for {statement_type} chunk {chunk_years}")

                logger.info(f"[SUCCESS] Processed chunk {chunk_years[0]}-{chunk_years[-1]} for {statement_type}")

            return RecognitionResult(
                success=True,
                statement_type=statement_type,
                extracted_data=consolidated_chunks
            )

        except Exception as e:
            logger.error(f"Failed to consolidate {statement_type}: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.CONSOLIDATION_FAILED}: Failed to consolidate {statement_type}: {str(e)}"
            ) 

    def _get_standardized_line_items(self, statement_type: str) -> Dict[str, str]:
        """Get standardized names for all line items in a statement type"""
        try:
            # Collect all unique line items across all statements
            all_line_items = set()
            for json_obj in self.extracted_jsons:
                if statement_type in json_obj.get("statements", {}):
                    for year_data in json_obj["statements"][statement_type].values():
                        all_line_items.update(year_data.keys())

            if not all_line_items:
                logger.info(f"No line items found for {statement_type}")
                return {}

            consolidation_model = genai.GenerativeModel(GEMINI_CONFIG["consolidation_model"])
            
            prompt = {
                "role": "user",
                "parts": [{
                    "text": f"""Create a standardized mapping for these financial statement line items.

Input items:
{sorted(list(all_line_items))}

Rules:
1. Output a valid JSON mapping where:
   - Keys are the original line items
   - Values are the standardized names

2. Standardize common variations:
   - "Profit/Loss" → "Profit" (e.g., "Operating Profit/Loss" → "Operating Profit")
   - "Gross Profit/Loss" → "Gross Profit"
   - Remove "For The Financial Year" suffix
   - Remove "On Ordinary Activities" where redundant
   - Merge variations of same concept (e.g., "Turnover" and "Net Turnover")
   - Standardize "Creditors" vs "Accounts Payable"
   - Standardize "Debtors" vs "Accounts Receivable"

3. Format rules:
   - Capitalize first letter of each word
   - Use spaces between words (not underscores)
   - Remove redundant words
   - Keep important distinctions (e.g., between different types of assets)

4. Handle special cases:
   - Preserve timing distinctions (e.g., "Within One Year" vs "After More Than One Year")
   - Keep important prefixes (e.g., "Net" vs "Gross")
   - Maintain asset/liability distinctions
   - Keep pension-related distinctions

Output format:
{{
    "original_name": "Standardized Name",
    "another_original": "Another Standard"
}}"""
                }]
            }

            response = consolidation_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "candidate_count": 1,
                    "max_output_tokens": 4096
                }
            )

            if not response or not response.text:
                raise ValueError(f"Empty response from API for {statement_type} line item standardization")

            # Clean and parse the response
            cleaned_response = response.text.strip()
            if cleaned_response.startswith('```'):
                start = cleaned_response.find('{')
                end = cleaned_response.rfind('}') + 1
                if start >= 0 and end > 0:
                    cleaned_response = cleaned_response[start:end]

            standardized_mapping = json.loads(cleaned_response)
            logger.info(f"[SUCCESS] Created standardized mapping for {len(standardized_mapping)} {statement_type} line items")
            return standardized_mapping

        except Exception as e:
            logger.error(f"Failed to standardize line items for {statement_type}: {str(e)}")
            return {} 