from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import io
from pdf2image import convert_from_bytes
from PIL import Image
import streamlit as st
import logging

logger = logging.getLogger(__name__)

@dataclass
class RecognitionResult:
    success: bool
    statement_type: Optional[str] = None
    confidence: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    image_bytes_list: List[bytes] = field(default_factory=list)

class DocumentUploader:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def recognize_document(self, file) -> RecognitionResult:
        try:
            file_content = file.read()
            file.seek(0)
            
            # Check file extension
            file_extension = file.name.lower().split('.')[-1]
            
            logger.info(f"\n=== Processing {file_extension.upper()} file ===")
            
            if file_extension == 'pdf':
                image_bytes_list = self._convert_to_image_bytes(file_content, file.name)
            else:  # Handle image files directly
                image_bytes_list = self._process_image_file(file_content)
            
            if not image_bytes_list:
                return RecognitionResult(
                    success=False,
                    error=f"Failed to process {file.name}"
                )

            logger.info(f"Processed {len(image_bytes_list)} pages/images")
            
            return RecognitionResult(
                success=True,
                statement_type="Financial Statement",
                confidence=1.0,
                extracted_data={"pages": len(image_bytes_list)},
                image_bytes_list=image_bytes_list
            )
            
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return RecognitionResult(
                success=False,
                error=f"File processing failed: {str(e)}"
            )

    def _convert_to_image_bytes(self, pdf_bytes: bytes, filename: str) -> List[bytes]:
        try:
            # Convert all pages
            images = convert_from_bytes(
                pdf_bytes,
                fmt='jpeg',
                grayscale=False,
                size=(1500, None),
                use_cropbox=True
            )
            
            logger.info(f"Converting {len(images)} pages from PDF")
            
            image_bytes_list = []
            for i, img in enumerate(images, 1):
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                image_bytes_list.append(img_byte_arr.getvalue())
                logger.info(f"Converted page {i}")
            
            return image_bytes_list
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            return [] 

    def _process_image_file(self, image_bytes: bytes) -> List[bytes]:
        """Handle direct image file processing"""
        try:
            # Open the image using PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (in case of PNG with transparency)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Convert to JPEG bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            
            return [img_byte_arr.getvalue()]
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            return [] 