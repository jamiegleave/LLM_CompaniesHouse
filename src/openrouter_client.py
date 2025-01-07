from dataclasses import dataclass
from typing import Optional, Dict, List
import openai
import base64
import json
import logging
from .config import OPENROUTER_CONFIG, ErrorCodes, ERROR_MESSAGES

# Configure logging with a cleaner format
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Only show the message
)
logger = logging.getLogger(__name__)

@dataclass
class RecognitionResult:
    success: bool
    statement_type: Optional[str] = None
    confidence: Optional[float] = None
    extracted_data: Optional[Dict] = None
    error: Optional[str] = None

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_CONFIG["api_base"],
            timeout=OPENROUTER_CONFIG["timeout"]
        )
        self.default_model = OPENROUTER_CONFIG["default_model"]
        self.max_retries = OPENROUTER_CONFIG["max_retries"]

    def analyze_document(self, image_bytes_list: List[bytes]) -> RecognitionResult:
        """Analyze financial statement using Vision API"""
        try:
            if not image_bytes_list:
                logger.error("No images provided")
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.RECOGNITION_FAILED}: No images provided"
                )

            # Log basic request info
            logger.info("\n=== Document Analysis ===")
            logger.info(f"Total pages: {len(image_bytes_list)}")

            # First, identify which pages contain financial statements
            financial_pages = self._identify_financial_pages(image_bytes_list)
            if not financial_pages:
                return RecognitionResult(
                    success=False,
                    error=f"{ErrorCodes.RECOGNITION_FAILED}: No financial statements found"
                )

            logger.info(f"Found financial statements on pages: {financial_pages.keys()}")

            # Process each identified financial page
            results = {}
            for page_type, page_index in financial_pages.items():
                logger.info(f"\n=== Processing {page_type} ===")
                page_result = self._analyze_financial_page(
                    image_bytes_list[page_index],
                    page_type
                )
                results[page_type] = page_result

            return RecognitionResult(
                success=True,
                statement_type="Multiple",
                confidence=1.0,
                extracted_data=results
            )

        except Exception as e:
            logger.error(f"\nDocument analysis failed: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"{ErrorCodes.RECOGNITION_FAILED}: {str(e)}"
            )

    def _identify_financial_pages(self, image_bytes_list: List[bytes]) -> Dict[str, int]:
        """Identify pages containing financial statements"""
        financial_pages = {}
        
        system_prompt = """You are a financial document analyzer. Examine this page and identify if it contains financial statements or tables.

Important indicators to look for:
1. Financial statement headers (e.g., "Balance Sheet", "Profit and Loss", "Income Statement")
2. Tabular data with currency amounts
3. Columns showing current and comparative years
4. Line items typical of financial statements (e.g., assets, liabilities, turnover, profit)

Respond with one of:
"STATEMENT: PROFIT_LOSS" if you find a profit & loss / income statement
"STATEMENT: BALANCE_SHEET" if you find a balance sheet
"STATEMENT: NONE" if no financial statements are found"""

        for i, image_bytes in enumerate(image_bytes_list):
            logger.info(f"\n=== Analyzing Page {i+1} ===")
            
            try:
                # Convert image to base64 with proper data URI format
                base64_image = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                
                # Log request details (for debugging)
                logger.info(f"Making API request for page {i+1}")
                logger.info(f"Using model: {self.default_model}")
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.default_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": [
                                {
                                    "type": "text",
                                    "text": "Does this page contain any formal financial statements?"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": base64_image
                                    }
                                }
                            ]}
                        ],
                        max_tokens=50,
                        temperature=0.1
                    )
                    
                    # Add error checking for API error response
                    if hasattr(response, 'error'):
                        error_msg = response.error.get('message', 'Unknown API error')
                        error_code = response.error.get('code', 'unknown')
                        logger.error(f"API Error (code {error_code}): {error_msg}")
                        continue
                    
                    # Log raw API response (for debugging)
                    logger.info(f"Raw API response: {response}")
                    
                    if not response:
                        logger.error("API returned None response")
                        continue
                        
                    if not hasattr(response, 'choices'):
                        logger.error(f"Unexpected response structure: {response}")
                        continue
                        
                    if not response.choices:
                        logger.error("No choices in response")
                        continue
                        
                    if not response.choices[0].message:
                        logger.error("No message in first choice")
                        continue
                        
                    content = response.choices[0].message.content
                    if not content:
                        logger.error("Empty content in message")
                        continue
                        
                    content = content.strip().upper()
                    logger.info(f"API Response for page {i+1}: {content}")
                    
                    if "PROFIT_LOSS" in content:
                        financial_pages["Profit and Loss"] = i
                        logger.info(f"Found Profit and Loss statement on page {i+1}")
                    elif "BALANCE_SHEET" in content:
                        financial_pages["Balance Sheet"] = i
                        logger.info(f"Found Balance Sheet on page {i+1}")
                        
                except Exception as api_error:
                    logger.error(f"API request failed: {str(api_error)}")
                    logger.error(f"API error type: {type(api_error)}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error processing page {i+1}: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                continue
        
        if not financial_pages:
            logger.info("No financial statements found")
        else:
            logger.info(f"Found financial statements: {financial_pages}")
            
        return financial_pages

    def _analyze_financial_page(self, image_bytes: bytes, page_type: str) -> Dict:
        """Analyze a page containing financial data"""
        logger.info(f"\n=== Analyzing Financial Data ===")
        
        base64_image = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        
        system_prompt = """You are a financial data extraction expert. Extract ALL line items from these financial statements into structured JSON, maintaining exact numbers, signs, relationships, and units for both current and comparative years.

Key Requirements:
1. Structure:
{
    "metadata": {
        "currency": "GBP",  // The currency used (e.g., GBP, USD, EUR)
        "scale": "millions", // Whether numbers are in thousands, millions, etc.
        "unit_symbol": "£m"  // The unit symbol shown on the statement
    },
    "2023": {
        "profit_and_loss": [
            {"name": "Turnover", "value": 11207},
            {"name": "Cost of sales", "value": -10801},
            // ... all line items in order
        ],
        "balance_sheet": {
            "fixed_assets": [...],
            "current_assets": [...],
            // ... other sections
        }
    },
    "2022": {
        // Same structure as 2023
    }
}

2. Data Rules:
- First identify and extract the currency and scale from the statement
- Extract EVERY line item exactly as shown
- Convert all values to numbers at the scale shown (e.g., if in millions, use millions)
- Use negative numbers for expenses/liabilities
- Remove currency symbols from values but capture in metadata
- Round to 3 decimal places
- Maintain exact ordering from statements

3. Required Sections:
- metadata: Currency and scale information
- profit_and_loss: Array of all P&L items
- balance_sheet (when present):
  - fixed_assets
  - current_assets
  - current_liabilities
  - net_current_assets
  - total_assets_less_current_liabilities
  - long_term_liabilities
  - capital_and_reserves

4. Validation:
- All values must match statement exactly
- Include both years for all items
- Maintain mathematical relationships
- Use consistent sign conventions
- Units must match those shown on statement

Respond ONLY with the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {
                            "type": "text",
                            "text": "Extract all financial data from this statement into JSON format, maintaining exact values and relationships."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            }
                        }
                    ]}
                ],
                max_tokens=4000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if not response.choices or not response.choices[0].message:
                logger.error("Empty response from API")
                return None
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty content in response")
                return None
            
            logger.info(f"Raw API response content: {content}")
            
            try:
                content = content.strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                    
                parsed_data = json.loads(content)
                
                # Validate the parsed data structure
                if not isinstance(parsed_data, dict):
                    logger.error("Invalid data structure: not a dictionary")
                    return None
                    
                # Check for required top-level keys
                if "metadata" not in parsed_data:
                    logger.error("Invalid data structure: missing metadata")
                    return None
                    
                # Validate metadata structure
                required_metadata = ["currency", "scale", "unit_symbol"]
                if not all(key in parsed_data["metadata"] for key in required_metadata):
                    logger.error("Invalid data structure: incomplete metadata")
                    return None
                    
                # Check for year keys (excluding metadata)
                years = [key for key in parsed_data.keys() if key != "metadata"]
                if not years or not all(str(year).isdigit() for year in years):
                    logger.error("Invalid data structure: missing or invalid year keys")
                    return None
                    
                # Validate structure for each year
                for year in years:
                    if not isinstance(parsed_data[year], dict):
                        logger.error(f"Invalid structure for year {year}")
                        return None
                        
                    if page_type == "Profit and Loss" and "profit_and_loss" not in parsed_data[year]:
                        logger.error(f"Missing profit_and_loss section in year {year}")
                        return None
                        
                    if page_type == "Balance Sheet" and "balance_sheet" not in parsed_data[year]:
                        logger.error(f"Missing balance_sheet section in year {year}")
                        return None
                
                logger.info("Successfully parsed and validated JSON response")
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Attempted to parse content: {content}")
                return None
                
        except Exception as e:
            logger.error(f"Error during financial data extraction: {str(e)}")
            return None

    def _process_response(self, response) -> Dict:
        """Process and validate API response"""
        try:
            logger.info("\n=== Processing Response ===")
            
            if not response.choices or not response.choices[0].message:
                logger.error("Invalid response structure")
                raise ValueError("Invalid API response structure")

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response content")
                raise ValueError("Empty response content")

            # Parse JSON response
            if isinstance(content, str):
                try:
                    parsed_data = json.loads(content)
                    # Validate structure
                    self._validate_financial_data(parsed_data)
                    logger.info("Successfully parsed and validated JSON response")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed: {str(e)}")
                    raise ValueError("Could not parse response as JSON")
            else:
                parsed_data = content
                self._validate_financial_data(parsed_data)
                logger.info("Received and validated pre-parsed response")
                return parsed_data

        except Exception as e:
            logger.error(f"Response processing failed: {str(e)}")
            raise ValueError(f"Failed to process response: {str(e)}")

    def _validate_financial_data(self, data: Dict) -> None:
        """Validate the structure and content of the financial data"""
        required_sections = ['profit_and_loss', 'balance_sheet']
        
        # Check years exist
        if not any(str(year).isdigit() for year in data.keys()):
            raise ValueError("No valid years found in data")
            
        for year in data.keys():
            if not isinstance(data[year], dict):
                raise ValueError(f"Invalid structure for year {year}")
                
            # Check required sections exist
            for section in required_sections:
                if section not in data[year]:
                    raise ValueError(f"Missing {section} section in year {year}")
                    
            # Validate balance sheet structure
            balance_sheet = data[year]['balance_sheet']
            required_bs_sections = [
                'fixed_assets',
                'current_assets',
                'current_liabilities',
                'net_current_assets',
                'total_assets_less_current_liabilities',
                'long_term_liabilities',
                'capital_and_reserves'
            ]
            
            for section in required_bs_sections:
                if section not in balance_sheet:
                    raise ValueError(f"Missing {section} in balance sheet for year {year}") 