# Supported file formats
SUPPORTED_FORMATS = ["pdf", "png", "jpg", "jpeg", "webp", "heic", "heif"]

# Maximum file size in MB (Gemini supports up to 2GB per file)
MAX_FILE_SIZE_MB = 2048

# Preview image size (Gemini scales images between 768x768 and 3072x3072)
PREVIEW_WIDTH = 1024

# Error codes
class ErrorCodes:
    FILE_TOO_LARGE = "E001"
    UNSUPPORTED_FORMAT = "E002"
    CORRUPTED_FILE = "E003"
    PROCESSING_ERROR = "E004"
    API_ERROR = "E005"
    INVALID_API_KEY = "E006"
    RECOGNITION_FAILED = "E007"
    CONSOLIDATION_FAILED = "CONSOLIDATION_FAILED"
    INVALID_JSON = "INVALID_JSON"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"

# Error messages
ERROR_MESSAGES = {
    ErrorCodes.FILE_TOO_LARGE: "File size exceeds maximum limit of 2GB",
    ErrorCodes.UNSUPPORTED_FORMAT: "Unsupported file format",
    ErrorCodes.CORRUPTED_FILE: "File appears to be corrupted",
    ErrorCodes.PROCESSING_ERROR: "Error processing file",
    ErrorCodes.API_ERROR: "API request failed",
    ErrorCodes.INVALID_API_KEY: "Invalid API key",
    ErrorCodes.RECOGNITION_FAILED: "Document recognition failed"
}

# Gemini Configuration
GEMINI_CONFIG = {
    "analysis_model": "gemini-1.5-flash-8b",  # For document analysis
    "consolidation_model": "gemini-1.5-pro",   # For statement consolidation
    "timeout": 600,  # 10 minutes timeout for large documents
    "max_retries": 3,
    "image_mime_types": {  # Supported image MIME types
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg", 
        "webp": "image/webp",
        "heic": "image/heic",
        "heif": "image/heif"
    }
} 