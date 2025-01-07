Here's a specification for a Python-based application using Streamlit:

**1. Application Concept & Core Functionality**

Name: FinState Analyzer
Purpose: LLM-powered financial statement extraction and validation tool

Core Functions:
- PDF/Image upload of financial statements
- Automated extraction using LLM vision models
- Built-in validation and confidence scoring
- Export to structured formats (JSON, CSV, Excel)
- Validation report generation

**2. UX/UI Requirements & User Flow**

Layout:
- Clean, minimal interface with sidebar navigation
- Progress indicators for processing steps
- Clear validation status indicators
- Interactive data tables for review
- API key configuration section

User Flow:
1. Initial Setup
   - Enter and validate API keys (stored securely in session state)
   - Optional: Save API keys locally for future sessions

2. Upload Document(s)
   - Drag & drop or file select
   - Preview uploaded document(s)
   - Show batch processing status if multiple files

3. Processing View
   - Show extraction progress
   - Display confidence scores
   - Show validation checks in real-time

4. Review & Edit
   - Interactive tables for each statement
   - Highlight validation issues
   - Allow manual corrections

5. Export & Report
   - Choose export format
   - Generate validation report
   - Download options

**3. Key Features (Priority Order)**

Phase 1 (MVP):
1. Document upload and basic extraction
2. Core financial statement recognition
3. Basic validation rules
4. Simple JSON export

Phase 2:
5. Enhanced validation system
6. Confidence scoring
7. Secondary LLM verification
8. Excel/CSV export options

Phase 3:
9. Historical comparison
10. Custom validation rules
11. Batch processing
12. API integration

**4. Technical Stack**

Framework:
- Streamlit (frontend/UI)

Required Libraries:
- streamlit
- python-multipart
- PyPDF2
- Pillow
- pandas
- openai
- openpyxl
- numpy
- pytest (testing)
- concurrent.futures (parallel processing)
- tqdm (progress tracking)

API Configuration:
- OpenRouter API integration for LLM access
  - Base URL: https://openrouter.ai/api/v1
  - Supported models:
    - google/gemini-flash-1.5
    - Additional models as needed

Environment Variables:
- OPENROUTER_API_KEY: API key for OpenRouter access

**5. Data Inputs & Extraction Requirements**

Document Structure:
- Input PDFs typically contain:
  1. Preamble sections (e.g., Directors' Report, Business Review)
  2. Key Financial Statements:
     - Profit & Loss Account (Income Statement)
     - Balance Sheet
     - Supporting Notes

Extraction Targets:
1. Profit & Loss Metrics:
   - Turnover figures (Gross, Net)
   - Operating costs (Cost of Sales, Distribution, Administrative)
   - Profit metrics (Gross, Operating, Before/After Tax)
   - Financial items (Interest Receivable/Payable)
   - Year-on-year comparisons

2. Balance Sheet Metrics:
   - Fixed Assets (Tangible, Intangible, Investments)
   - Current Assets (Stock, Debtors, Cash)
   - Liabilities (Current, Long-term)
   - Capital and Reserves
   - Supporting totals and subtotals

Extraction Challenges:
- Variable document layouts and formatting
- Inconsistent table structures
- Mixed text and numeric content
- Multiple year comparisons
- Notes and references
- Image quality variations

Validation Requirements:
- Mathematical accuracy (e.g., subtotals match components)
- Cross-statement consistency
- Year-over-year reasonableness
- Standard accounting relationships
- Reference number verification

**6. Data Inputs & User Stories**

Data Inputs:
- PDF financial statements
- Image files (PNG, JPEG)
- Historical data (JSON/CSV)
- Validation rules config
- Company metadata

User Stories:

As a Financial Analyst, I want to:
- Upload multiple years of statements for processing
- Get immediate feedback on data quality
- Export structured data for analysis
- Save and reload previous extractions

As a Data Validator, I want to:
- Review extraction confidence scores
- See validation rule results
- Make manual corrections
- Generate validation reports

As a System Admin, I want to:
- Monitor system performance
- Configure validation rules
- Manage historical data
- Control access permissions