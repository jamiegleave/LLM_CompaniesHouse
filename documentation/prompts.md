
#### 1. Document Upload Component

```markdown
Please implement the document upload component for the FinState Analyzer with the following requirements:

**Implementation Requirements:**
- Create a Streamlit file uploader supporting PDF and image files (PNG, JPEG)
- Implement file validation (type, size, corruption checks)
- Add preview functionality for uploaded documents
- Include progress indicator for upload status
- Handle batch uploads with concurrent processing

**Error Handling:**
- Validate file types before processing
- Implement graceful failure for corrupted files
- Add user feedback for invalid uploads
- Include retry mechanism for failed uploads

**Testing Procedures:**
- Unit tests for file validation
- Integration tests for upload workflow
- Edge case testing (large files, invalid formats)
- Performance testing for batch uploads

**Documentation Updates:**
- Update README.md with upload specifications
- Add error codes to bugs.md
- Document file size limits and supported formats

**Project Context:**
This component is part of the UK Companies FinMetrics project, focusing on the initial data ingestion phase for Companies House documents.
```

#### 2. Core Financial Statement Recognition

```markdown
Please implement the financial statement recognition system with the following requirements:

**Implementation Requirements:**
- Integrate OpenRouter API for LLM access
- Configure OpenAI Vision API through OpenRouter
- Create statement type classification (Balance Sheet, P&L, etc.)
- Implement text extraction and structured data parsing
- Add confidence scoring for extracted data
- Include progress tracking for processing steps
- Support multiple LLM models via OpenRouter

**Error Handling:**
- Handle API timeout/failure scenarios
- Implement retry logic for failed API calls
- Add validation for extracted data format
- Include fallback processing options
- Handle OpenRouter-specific error responses
- Validate API key and headers

**Testing Procedures:**
- Unit tests for each recognition component
- Integration tests with OpenRouter API
- Mock API responses for testing
- Accuracy testing with sample documents
- Performance benchmarking
- Test different LLM models

**Documentation Updates:**
- Add OpenRouter API integration details to README.md
- Document recognition patterns in technical docs
- Update changelog.md with new features
- Include OpenRouter configuration guide
- Document supported models and their capabilities

**Project Context:**
This component handles the core document understanding for Companies House financial statements using OpenRouter as the API gateway for LLM access, requiring high accuracy and reliability.
```

#### 3. Basic Validation Rules Engine

```markdown
Please implement the validation rules engine with the following requirements:

**Implementation Requirements:**
- Create configurable validation rule framework
- Implement basic financial statement validation rules
- Add real-time validation checking
- Include validation status indicators
- Create validation summary reports

**Error Handling:**
- Handle invalid rule configurations
- Implement validation failure logging
- Add user notification system
- Include validation override options

**Testing Procedures:**
- Unit tests for each validation rule
- Integration tests for rule engine
- Performance testing with large datasets
- Edge case validation testing

**Documentation Updates:**
- Document validation rules in README.md
- Add validation error codes to bugs.md
- Update technical documentation with rule specifications

**Project Context:**
This component ensures data quality for Companies House metrics, requiring robust validation checks and clear error reporting.
```

#### 4. JSON Export System

```markdown
Please implement the JSON export system with the following requirements:

**Implementation Requirements:**
- Create standardized JSON schema for financial data
- Implement export functionality with formatting options
- Add batch export capabilities
- Include export progress tracking
- Create export validation checks

**Error Handling:**
- Validate JSON structure before export
- Handle large dataset exports
- Implement export retry mechanism
- Add corrupt data detection

**Testing Procedures:**
- Unit tests for JSON formatting
- Integration tests for export workflow
- Performance testing with large datasets
- Schema validation testing

**Documentation Updates:**
- Document JSON schema in README.md
- Add export specifications to technical docs
- Update changelog.md with export features

**Project Context:**
This component provides standardized data export for Companies House metrics, requiring consistent formatting and reliable performance.
```
