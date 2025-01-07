import pytest
from pathlib import Path
import io
from PIL import Image
import sys
from ..src.document_uploader import DocumentUploader
from ..src.config import ErrorCodes, ERROR_MESSAGES

# Point to actual downloads directory
DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"

class TestPDFProcessing:
    class RealFile:
        def __init__(self, path):
            self.path = path
            self.name = path.name
            self._file = open(path, 'rb')
            self._file.seek(0, io.SEEK_END)
            self.size = self._file.tell()
            self._file.seek(0)
            print(f"File size: {self.size:,} bytes")

        def read(self, size=-1):
            data = self._file.read(size)
            print(f"Read {len(data):,} bytes")
            return data

        def seek(self, pos):
            print(f"Seeking to position {pos}")
            self._file.seek(pos)

        def close(self):
            self._file.close()

    @pytest.fixture
    def uploader(self):
        """Create a DocumentUploader instance"""
        # For testing PDF processing only, skip API calls
        class TestUploader(DocumentUploader):
            def recognize_document(self, file):
                # Override to skip API call
                try:
                    file_bytes = file.read()
                    file.seek(0)
                    # Just test the PDF conversion
                    image_bytes_list = self._convert_to_image_bytes(file_bytes, file.name)
                    success = len(image_bytes_list) > 0
                    
                    # Return a RecognitionResult object to match real implementation
                    from dataclasses import dataclass
                    
                    @dataclass
                    class RecognitionResult:
                        success: bool
                        statement_type: str = None
                        confidence: float = None
                        extracted_data: dict = None
                        error: str = None
                    
                    if success:
                        return RecognitionResult(
                            success=True,
                            statement_type="Test",
                            confidence=1.0,
                            extracted_data={"pages": len(image_bytes_list)}
                        )
                    else:
                        return RecognitionResult(
                            success=False,
                            error="Failed to convert PDF to images"
                        )
                        
                except Exception as e:
                    return RecognitionResult(
                        success=False,
                        error=f"Error processing file: {str(e)}"
                    )

        return TestUploader(api_key="dummy_key")

    def test_pdf_conversion(self, uploader):
        """Test conversion of PDFs to images"""
        pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))
        print(f"\nStarting PDF conversion test")
        print(f"Found {len(pdf_files)} PDF files in: {DOWNLOADS_DIR}")
        print(f"PDF files: {[f.name for f in pdf_files]}")
        
        if not pdf_files:
            pytest.skip("No PDF files found in downloads directory")
        
        for pdf_path in pdf_files:
            print(f"\n{'='*80}")
            print(f"PROCESSING: {pdf_path.name}")
            
            # Read the file
            with open(pdf_path, 'rb') as file:
                file_bytes = file.read()
            print(f"1. File read complete: {len(file_bytes)} bytes")
            
            try:
                # Step 1: PyPDF Check
                print("\n2. Attempting PyPDF check...")
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                print(f"   ✓ PyPDF read successful: {len(reader.pages)} pages")
                
                # Step 2: pdf2image Check
                print("\n3. Attempting pdf2image conversion...")
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(
                    file_bytes,
                    fmt='jpeg',
                    grayscale=False,
                    size=(1500, None),
                    use_cropbox=True
                )
                print(f"   ✓ pdf2image conversion successful: {len(images)} pages")
                
                # Step 3: DocumentUploader Check
                print("\n4. Attempting DocumentUploader conversion...")
                image_bytes_list = uploader._convert_to_image_bytes(file_bytes, pdf_path.name)
                print(f"   ✓ DocumentUploader conversion successful: {len(image_bytes_list)} images")
                
                # Step 4: Verify Images
                print("\n5. Verifying converted images...")
                for i, page_bytes in enumerate(image_bytes_list):
                    image = Image.open(io.BytesIO(page_bytes))
                    print(f"   ✓ Page {i+1}: {image.format} format, {image.mode} mode, {image.size} size")
                
                print(f"\n✓ SUCCESS: {pdf_path.name} fully processed")
                
            except Exception as e:
                print(f"\n❌ ERROR processing {pdf_path.name}")
                print(f"Error type: {type(e)}")
                print(f"Error message: {str(e)}")
                import traceback
                print(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
                pytest.fail(f"Failed to process {pdf_path.name}: {str(e)}")

    def test_pdf_validation(self, uploader):
        """Test validation of PDFs"""
        pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))
        print(f"\nStarting PDF validation test")
        print(f"Found {len(pdf_files)} PDF files to validate")
        
        if not pdf_files:
            pytest.skip("No PDF files found in downloads directory")
        
        for pdf_path in pdf_files:
            print(f"\n{'='*80}")
            print(f"VALIDATING: {pdf_path.name}")
            
            class RealFile:
                def __init__(self, path):
                    self.path = path
                    self.name = path.name
                    self._file = open(path, 'rb')
                    self._file.seek(0, io.SEEK_END)
                    self.size = self._file.tell()
                    self._file.seek(0)
                    print(f"File size: {self.size:,} bytes")

                def read(self, size=-1):
                    data = self._file.read(size)
                    print(f"Read {len(data):,} bytes")
                    return data

                def seek(self, pos):
                    print(f"Seeking to position {pos}")
                    self._file.seek(pos)

                def close(self):
                    self._file.close()
            
            file = RealFile(pdf_path)
            is_valid, error = uploader.validate_file(file)
            
            result = "✓ Valid" if is_valid else f"❌ Invalid: {error}"
            print(f"Result: {result}")
            file.close()

    def test_streamlit_upload_simulation(self, uploader):
        """Simulate how Streamlit handles file uploads"""
        pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))
        print(f"\nTesting Streamlit upload simulation")
        
        for pdf_path in pdf_files:
            print(f"\n{'='*80}")
            print(f"PROCESSING: {pdf_path.name}")
            
            # Read file as bytes first
            with open(pdf_path, 'rb') as f:
                file_bytes = f.read()
            
            # Create a BytesIO object to simulate Streamlit's UploadedFile
            file_like = io.BytesIO(file_bytes)
            file_like.name = pdf_path.name
            
            # Process using DocumentUploader
            try:
                result = uploader.recognize_document(file_like)
                print(f"Recognition result: {result}")
                assert result.success, f"Recognition failed: {result.error}"
                
            except Exception as e:
                print(f"\n❌ ERROR processing {pdf_path.name}")
                print(f"Error type: {type(e)}")
                print(f"Error message: {str(e)}")
                import traceback
                print(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
                pytest.fail(f"Failed to process {pdf_path.name}: {str(e)}")

    def test_file_content_integrity(self, uploader):
        """Test file content integrity through different reading methods"""
        pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))
        print(f"\nTesting file content integrity")
        
        for pdf_path in pdf_files:
            print(f"\n{'='*80}")
            print(f"CHECKING: {pdf_path.name}")
            
            # Method 1: Direct file read
            with open(pdf_path, 'rb') as f:
                direct_bytes = f.read()
            print(f"\n1. Direct file read:")
            print(f"   Size: {len(direct_bytes):,} bytes")
            print(f"   First 50 bytes: {direct_bytes[:50]}")
            
            # Method 2: BytesIO simulation
            file_like = io.BytesIO(direct_bytes)
            file_like.name = pdf_path.name
            bytes_io_content = file_like.read()
            print(f"\n2. BytesIO read:")
            print(f"   Size: {len(bytes_io_content):,} bytes")
            print(f"   First 50 bytes: {bytes_io_content[:50]}")
            
            # Method 3: RealFile simulation
            real_file = self.RealFile(pdf_path)
            real_file_content = real_file.read()
            print(f"\n3. RealFile read:")
            print(f"   Size: {len(real_file_content):,} bytes")
            print(f"   First 50 bytes: {real_file_content[:50]}")
            real_file.close()
            
            # Method 4: Multiple read simulation
            file_like = io.BytesIO(direct_bytes)
            file_like.name = pdf_path.name
            
            print("\n4. Multiple read simulation:")
            first_read = file_like.read()
            file_like.seek(0)
            second_read = file_like.read()
            print(f"   First read size: {len(first_read):,} bytes")
            print(f"   Second read size: {len(second_read):,} bytes")
            print(f"   Content identical: {first_read == second_read}")
            
            # Verify all methods produce the same content
            assert len(direct_bytes) == len(bytes_io_content) == len(real_file_content), "File sizes don't match"
            assert direct_bytes == bytes_io_content == real_file_content, "File contents don't match"
            assert first_read == second_read, "Multiple reads produce different content"
            
            print("\n✓ All content integrity checks passed")

    def test_streamlit_file_handling(self, uploader):
        """Test file handling with Streamlit-like conditions"""
        pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))
        
        for pdf_path in pdf_files:
            print(f"\n{'='*80}")
            print(f"Testing Streamlit handling: {pdf_path.name}")
            
            # Method 1: Normal file read
            with open(pdf_path, 'rb') as f:
                normal_bytes = f.read()
            
            # Method 2: Chunked read (like Streamlit might do)
            chunks = []
            with open(pdf_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # Streamlit's default chunk size
                    if not chunk:
                        break
                    chunks.append(chunk)
            chunked_bytes = b''.join(chunks)
            
            # Method 3: Line-by-line read
            lines = []
            with open(pdf_path, 'rb') as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
            line_bytes = b''.join(lines)
            
            # Compare methods
            print("\nFile size comparison:")
            print(f"Normal read: {len(normal_bytes):,} bytes")
            print(f"Chunked read: {len(chunked_bytes):,} bytes")
            print(f"Line read: {len(line_bytes):,} bytes")
            
            print("\nFirst 50 bytes comparison:")
            print(f"Normal: {normal_bytes[:50]}")
            print(f"Chunked: {chunked_bytes[:50]}")
            print(f"Line: {line_bytes[:50]}")
            
            # Test each version with pdf2image
            print("\nTesting PDF conversion with each method:")
            for method_name, content in [
                ("Normal", normal_bytes),
                ("Chunked", chunked_bytes),
                ("Line", line_bytes)
            ]:
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(content)
                    print(f"✓ {method_name} read conversion successful: {len(images)} pages")
                except Exception as e:
                    print(f"❌ {method_name} read conversion failed: {str(e)}") 