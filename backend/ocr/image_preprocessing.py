"""
Image preprocessing utilities for OCR.
Handles deskewing, denoising, contrast enhancement, and binarization.
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class ImagePreprocessor:
    """Preprocess images to improve OCR accuracy."""
    
    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """
        Deskew rotated image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Deskewed image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Create binary image
            binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # Find all non-zero points
            coords = np.column_stack(np.where(binary > 0))
            
            if len(coords) == 0:
                return image
            
            # Get angle using minimum area rectangle
            angle = cv2.minAreaRect(coords)[-1]
            
            # Correct angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Rotate image if angle is significant
            if abs(angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, 
                                        borderMode=cv2.BORDER_REPLICATE)
                return rotated
            
            return image
        except Exception as e:
            print(f"⚠️ Deskew error: {e}")
            return image
    
    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Denoised image
        """
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply bilateral filter (preserves edges while removing noise)
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            return denoised
        except Exception as e:
            print(f"⚠️ Denoise error: {e}")
            return image
    
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Contrast-enhanced image
        """
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            return enhanced
        except Exception as e:
            print(f"⚠️ Contrast enhancement error: {e}")
            return image
    
    @staticmethod
    def binarize(image: np.ndarray, method: str = "adaptive") -> np.ndarray:
        """
        Convert image to binary (black and white) for better OCR.
        
        Args:
            image: Input image as numpy array
            method: Binarization method ("adaptive", "otsu", or "simple")
            
        Returns:
            Binary image
        """
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            if method == "adaptive":
                # Adaptive thresholding (works well with varying lighting)
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
            elif method == "otsu":
                # Otsu's thresholding (automatically determines threshold)
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:
                # Simple thresholding
                _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            return binary
        except Exception as e:
            print(f"⚠️ Binarization error: {e}")
            return image
    
    @staticmethod
    def preprocess(image: np.ndarray, 
                   deskew: bool = True,
                   denoise: bool = True,
                   enhance_contrast: bool = True,
                   binarize: bool = True,
                   binarize_method: str = "adaptive") -> np.ndarray:
        """
        Apply full preprocessing pipeline.
        
        Args:
            image: Input image as numpy array
            deskew: Whether to deskew the image
            denoise: Whether to denoise the image
            enhance_contrast: Whether to enhance contrast
            binarize: Whether to binarize the image
            binarize_method: Binarization method
            
        Returns:
            Preprocessed image
        """
        processed = image.copy()
        
        if deskew:
            processed = ImagePreprocessor.deskew(processed)
        
        if denoise:
            processed = ImagePreprocessor.denoise(processed)
        
        if enhance_contrast:
            processed = ImagePreprocessor.enhance_contrast(processed)
        
        if binarize:
            processed = ImagePreprocessor.binarize(processed, binarize_method)
        
        return processed
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format."""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format."""
        if len(cv2_image.shape) == 2:
            return Image.fromarray(cv2_image)
        else:
            return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

