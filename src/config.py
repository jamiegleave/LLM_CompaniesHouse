# Supported file formats
SUPPORTED_FORMATS = ["pdf", "png", "jpg", "jpeg"]

# Maximum file size in MB
MAX_FILE_SIZE_MB = 10

# Preview image size
PREVIEW_WIDTH = 800

# Error codes
class ErrorCodes:
    FILE_TOO_LARGE = "E001"
    UNSUPPORTED_FORMAT = "E002"
    CORRUPTED_FILE = "E003"
    PROCESSING_ERROR = "E004"
    API_ERROR = "E005"
    INVALID_API_KEY = "E006"
    RECOGNITION_FAILED = "E007"

# Error messages
ERROR_MESSAGES = {
    ErrorCodes.FILE_TOO_LARGE: "File size exceeds maximum limit",
    ErrorCodes.UNSUPPORTED_FORMAT: "Unsupported file format",
    ErrorCodes.CORRUPTED_FILE: "File appears to be corrupted",
    ErrorCodes.PROCESSING_ERROR: "Error processing file",
    ErrorCodes.API_ERROR: "API request failed",
    ErrorCodes.INVALID_API_KEY: "Invalid API key",
    ErrorCodes.RECOGNITION_FAILED: "Document recognition failed"
}

# OpenRouter Configuration
OPENROUTER_CONFIG = {
    "api_base": "https://openrouter.ai/api/v1",
    "default_model": "google/gemini-flash-1.5-8b",
    "supported_models": [
        "google/gemini-flash-1.5-8b",
        "anthropic/claude-3-haiku",
        "anthropic/claude-3-sonnet"
    ],
    "timeout": 30,
    "max_retries": 3
} 