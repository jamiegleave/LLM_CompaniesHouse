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

                # Updated system prompt with UK Companies Act format
                system_prompt = """You are a financial data parser that outputs valid JSON following UK Companies Act format. Extract ALL financial data visible in the document.

STRUCTURE:
{
    "metadata": {
        "currency": "DETECT FROM DOCUMENT (e.g. GBP, USD, EUR, etc.)",
        "scale": "DETECT FROM DOCUMENT (e.g., millions, thousands, billions)",
        "unit_symbol": "DETECT FROM DOCUMENT (e.g., £m, £k, €B)"
    },
    "statements": {
        "profit_and_loss": {
            "YEAR": {
                // Format as per UK Companies Act:
                "Turnover": 0.0,
                "Cost of Sales": -0.0,
                "Gross Profit": 0.0,
                "Distribution Costs": -0.0,
                "Administrative Expenses": -0.0,
                "Other Operating Income": 0.0,
                "Operating Profit": 0.0,
                "Income from Shares in Group Undertakings": 0.0,
                "Income from Other Fixed Asset Investments": 0.0,
                "Interest Receivable and Similar Income": 0.0,
                "Interest Payable and Similar Charges": -0.0,
                "Profit Before Taxation": 0.0,
                "Tax on Profit": -0.0,
                "Profit for the Financial Year": 0.0
            }
        },
        "balance_sheet": {
            "YEAR": {
                // Fixed Assets
                "Intangible Fixed Assets": 0.0,
                "Tangible Fixed Assets": 0.0,
                "Fixed Asset Investments": 0.0,
                "Total Fixed Assets": 0.0,

                // Current Assets
                "Stocks": 0.0,
                "Debtors Due Within One Year": 0.0,
                "Debtors Due After One Year": 0.0,
                "Cash at Bank and In Hand": 0.0,
                "Total Current Assets": 0.0,

                // Liabilities
                "Creditors: Amounts Falling Due Within One Year": -0.0,
                "Net Current Assets": 0.0,
                "Total Assets Less Current Liabilities": 0.0,
                "Creditors: Amounts Falling Due After One Year": -0.0,
                "Provisions for Liabilities": -0.0,
                "Net Assets": 0.0,

                // Capital and Reserves
                "Called Up Share Capital": 0.0,
                "Share Premium Account": 0.0,
                "Revaluation Reserve": 0.0,
                "Other Reserves": 0.0,
                "Profit and Loss Account": 0.0,
                "Total Shareholders Funds": 0.0
            }
        }
    }
}

CRITICAL RULES:
1. Follow EXACT UK Companies Act terminology
2. Use negative numbers for:
   - All expenses and costs in P&L
   - Creditors and liabilities in balance sheet
3. Group items under correct categories
4. Maintain proper hierarchy
5. Keep timing distinctions (Within/After One Year)
6. Preserve group vs non-group distinctions
7. Use decimal numbers (e.g., 50.0 not 50)
8. Output valid JSON only
9. Include all years found in document
10. Standardize variations:
    - "Revenue" → "Turnover"
    - "Inventory" → "Stocks"
    - "Accounts Receivable" → "Debtors"
    - "Accounts Payable" → "Creditors"
    - "Net Income" → "Profit for the Financial Year"
"""

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

Rules:
1. Maintain UK Companies Act terminology (already standardized)
2. When multiple items map to the same name, combine their values
3. Preserve all unique line items
4. Keep negative numbers for expenses and liabilities

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