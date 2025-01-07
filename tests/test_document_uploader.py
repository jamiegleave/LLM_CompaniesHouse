import pytest
from io import BytesIO
from PIL import Image
import numpy as np
from ..src.document_uploader import DocumentUploader
from ..src.config import MAX_FILE_SIZE_MB, ErrorCodes, ERROR_MESSAGES

class MockFile:
    def __init__(self, name, size, content=None):
        self.name = name
        self.size = size
        self.content = content or BytesIO()

def test_validate_file_size():
    uploader = DocumentUploader()
    
    # Test file too large
    large_file = MockFile("test.pdf", (MAX_FILE_SIZE_MB + 1) * 1024 * 1024)
    is_valid, error = uploader.validate_file(large_file)
    assert not is_valid
    assert error == ERROR_MESSAGES[ErrorCodes.FILE_TOO_LARGE]

    # Test acceptable file size
    valid_file = MockFile("test.pdf", 1024 * 1024)  # 1MB
    is_valid, error = uploader.validate_file(valid_file)
    assert is_valid
    assert error is None

def test_validate_file_format():
    uploader = DocumentUploader()
    
    # Test invalid format
    invalid_file = MockFile("test.txt", 1024)
    is_valid, error = uploader.validate_file(invalid_file)
    assert not is_valid
    assert error == ERROR_MESSAGES[ErrorCodes.UNSUPPORTED_FORMAT]

    # Test valid formats
    valid_formats = ["test.pdf", "test.png", "test.jpg", "test.jpeg"]
    for filename in valid_formats:
        valid_file = MockFile(filename, 1024)
        is_valid, error = uploader.validate_file(valid_file)
        assert is_valid
        assert error is None 