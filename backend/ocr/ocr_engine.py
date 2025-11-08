"""
OCR Engine wrapper supporting Tesseract OCR and PaddleOCR.
Handles scanned PDF pages and provides confidence scoring.
"""
import os
from typing import List, Tuple, Optional, Dict
from PIL import Image
import numpy as np

# Try to import OCR libraries
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️ Tesseract OCR not available. Install: pip install pytesseract")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("⚠️ PaddleOCR not available. Install: pip install paddlepaddle paddleocr")

from .image_preprocessing import ImagePreprocessor


class OCREngine:
    """OCR Engine supporting multiple backends."""
    
    def __init__(self, engine: str = "paddleocr", lang: str = "en"):
        """
        Initialize OCR engine.
        
        Args:
            engine: OCR engine to use ("paddleocr", "tesseract", or "auto")
            lang: Language code (default: "en" for English)
        """
        self.engine = engine.lower()
        self.lang = lang
        self.preprocessor = ImagePreprocessor()
        
        # Initialize engines
        self.paddleocr_engine = None
        self.tesseract_available = TESSERACT_AVAILABLE
        
        if self.engine == "paddleocr" or self.engine == "auto":
            if PADDLEOCR_AVAILABLE:
                try:
                    # Initialize PaddleOCR (use_gpu=False by default, set to True if GPU available)
                    self.paddleocr_engine = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
                    print("✅ PaddleOCR initialized")
                except Exception as e:
                    print(f"⚠️ Failed to initialize PaddleOCR: {e}")
                    if self.engine == "paddleocr":
                        raise
            elif self.engine == "paddleocr":
                raise ImportError("PaddleOCR not available. Install: pip install paddlepaddle paddleocr")
        
        if self.engine == "tesseract" or (self.engine == "auto" and not PADDLEOCR_AVAILABLE):
            if not self.tesseract_available:
                raise ImportError("Tesseract OCR not available. Install: pip install pytesseract")
            print("✅ Tesseract OCR available")
    
    def _ocr_paddleocr(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Perform OCR using PaddleOCR.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        if self.paddleocr_engine is None:
            raise RuntimeError("PaddleOCR engine not initialized")
        
        try:
            # PaddleOCR expects numpy array
            result = self.paddleocr_engine.ocr(image, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            # Extract text and confidence scores
            texts = []
            confidences = []
            
            for line in result[0]:
                if line:
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1]
                    texts.append(text)
                    confidences.append(confidence)
            
            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except Exception as e:
            print(f"⚠️ PaddleOCR error: {e}")
            return "", 0.0
    
    def _ocr_tesseract(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Perform OCR using Tesseract OCR.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        if not self.tesseract_available:
            raise RuntimeError("Tesseract OCR not available")
        
        try:
            # Convert to PIL Image
            pil_image = ImagePreprocessor.cv2_to_pil(image)
            
            # Run OCR with confidence data
            ocr_data = pytesseract.image_to_data(pil_image, lang=self.lang, output_type=pytesseract.Output.DICT)
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip():
                    texts.append(text)
                    conf = int(ocr_data['conf'][i])
                    if conf > 0:  # Tesseract uses -1 for non-text elements
                        confidences.append(conf)
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0  # Normalize to 0-1
            
            return full_text, avg_confidence
            
        except Exception as e:
            print(f"⚠️ Tesseract OCR error: {e}")
            return "", 0.0
    
    def extract_text(self, image: np.ndarray, 
                     preprocess: bool = True,
                     preprocess_options: Optional[Dict] = None) -> Tuple[str, float]:
        """
        Extract text from image using OCR.
        
        Args:
            image: Image as numpy array or PIL Image
            preprocess: Whether to preprocess image before OCR
            preprocess_options: Options for preprocessing
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            image = np.array(image)
            if len(image.shape) == 3:
                image = ImagePreprocessor.pil_to_cv2(Image.fromarray(image))
        
        # Preprocess image
        if preprocess:
            options = preprocess_options or {}
            image = self.preprocessor.preprocess(image, **options)
        
        # Choose OCR engine
        if self.engine == "paddleocr" and self.paddleocr_engine:
            return self._ocr_paddleocr(image)
        elif self.engine == "tesseract" or (self.engine == "auto" and not self.paddleocr_engine):
            return self._ocr_tesseract(image)
        else:
            raise RuntimeError(f"OCR engine '{self.engine}' not available")
    
    def extract_text_from_pil(self, pil_image: Image.Image, 
                              preprocess: bool = True) -> Tuple[str, float]:
        """
        Extract text from PIL Image.
        
        Args:
            pil_image: PIL Image object
            preprocess: Whether to preprocess image before OCR
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        return self.extract_text(pil_image, preprocess=preprocess)


def detect_text_in_pdf(pdf_path: str, sample_pages: int = 3) -> bool:
    """
    Detect if PDF contains extractable text or is scanned images.
    
    Args:
        pdf_path: Path to PDF file
        sample_pages: Number of pages to sample
        
    Returns:
        True if PDF has text layer, False if scanned images
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_check = min(sample_pages, total_pages)
        
        text_found = False
        for page_num in range(pages_to_check):
            page = doc[page_num]
            text = page.get_text().strip()
            if len(text) > 50:  # Significant text found
                text_found = True
                break
        
        doc.close()
        return text_found
        
    except Exception as e:
        print(f"⚠️ Error detecting text in PDF: {e}")
        return False  # Assume scanned if we can't determine

