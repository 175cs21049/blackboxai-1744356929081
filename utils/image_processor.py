"""
Image preprocessing utilities for deepfake detection
Handles image loading, preprocessing, augmentation, and visualization
"""

import cv2
import numpy as np
from PIL import Image
import io
import base64


class ImageProcessor:
    """
    Handles all image preprocessing operations for deepfake detection
    """
    
    def __init__(self, target_size=(256, 256)):
        self.target_size = target_size
    
    def load_image_from_file(self, file_storage):
        """
        Load image from Flask file storage
        
        Args:
            file_storage: Flask FileStorage object
            
        Returns:
            numpy array: Loaded image in RGB format
        """
        # Read image bytes
        image_bytes = file_storage.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        return image_array
    
    def load_image_from_path(self, image_path):
        """
        Load image from file path
        
        Args:
            image_path: Path to image file
            
        Returns:
            numpy array: Loaded image in RGB format
        """
        # Read image using OpenCV
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    def preprocess_image(self, image, normalize=True):
        """
        Preprocess image for model input
        
        Args:
            image: Input image (numpy array)
            normalize: Whether to normalize pixel values to [0, 1]
            
        Returns:
            numpy array: Preprocessed image
        """
        # Resize to target size
        if image.shape[:2] != self.target_size:
            image = cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
        
        # Normalize pixel values
        if normalize:
            image = image.astype(np.float32) / 255.0
        
        return image
    
    def preprocess_for_detection(self, file_storage):
        """
        Complete preprocessing pipeline for detection
        
        Args:
            file_storage: Flask FileStorage object
            
        Returns:
            numpy array: Preprocessed image ready for model
        """
        # Load image
        image = self.load_image_from_file(file_storage)
        
        # Preprocess
        processed = self.preprocess_image(image, normalize=True)
        
        return processed
    
    def extract_face_region(self, image):
        """
        Extract face region from image using OpenCV face detection
        
        Args:
            image: Input image
            
        Returns:
            numpy array: Cropped face region or original image if no face found
        """
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # If face found, crop to face region with padding
        if len(faces) > 0:
            # Get largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            
            # Add padding
            padding = int(0.2 * max(w, h))
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            # Crop face region
            face_region = image[y1:y2, x1:x2]
            
            return face_region
        
        # Return original image if no face detected
        return image
    
    def augment_image(self, image):
        """
        Apply data augmentation for training
        
        Args:
            image: Input image
            
        Returns:
            numpy array: Augmented image
        """
        # Random horizontal flip
        if np.random.random() > 0.5:
            image = cv2.flip(image, 1)
        
        # Random brightness adjustment
        if np.random.random() > 0.5:
            factor = np.random.uniform(0.8, 1.2)
            image = np.clip(image * factor, 0, 255).astype(np.uint8)
        
        # Random rotation
        if np.random.random() > 0.5:
            angle = np.random.uniform(-15, 15)
            h, w = image.shape[:2]
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            image = cv2.warpAffine(image, M, (w, h))
        
        return image
    
    def create_heatmap_overlay(self, image, heatmap, alpha=0.4):
        """
        Create heatmap overlay on image for visualization
        
        Args:
            image: Original image
            heatmap: Heatmap array (same size as image)
            alpha: Transparency of overlay
            
        Returns:
            numpy array: Image with heatmap overlay
        """
        # Normalize heatmap
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Convert to RGB
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Resize heatmap to match image size
        if heatmap_colored.shape[:2] != image.shape[:2]:
            heatmap_colored = cv2.resize(
                heatmap_colored,
                (image.shape[1], image.shape[0])
            )
        
        # Ensure image is in correct format
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        # Blend images
        overlay = cv2.addWeighted(image, 1-alpha, heatmap_colored, alpha, 0)
        
        return overlay
    
    def image_to_base64(self, image):
        """
        Convert image to base64 string for web display
        
        Args:
            image: Image array
            
        Returns:
            str: Base64 encoded image string
        """
        # Ensure image is in correct format
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Encode to base64
        img_str = base64.b64encode(buffer.read()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def batch_preprocess(self, file_storages):
        """
        Preprocess multiple images at once
        
        Args:
            file_storages: List of Flask FileStorage objects
            
        Returns:
            numpy array: Batch of preprocessed images
        """
        images = []
        
        for file_storage in file_storages:
            try:
                image = self.preprocess_for_detection(file_storage)
                images.append(image)
            except Exception as e:
                print(f"Error processing image: {e}")
                continue
        
        if len(images) == 0:
            return None
        
        return np.array(images)
    
    def detect_image_manipulation(self, image):
        """
        Detect potential image manipulation artifacts
        Uses Error Level Analysis (ELA) technique
        
        Args:
            image: Input image
            
        Returns:
            numpy array: ELA result showing potential manipulation areas
        """
        # Convert to PIL Image
        if isinstance(image, np.ndarray):
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Save with compression
        buffer1 = io.BytesIO()
        pil_image.save(buffer1, 'JPEG', quality=90)
        buffer1.seek(0)
        
        # Reload compressed image
        compressed = Image.open(buffer1)
        
        # Calculate difference
        ela = np.array(pil_image).astype(np.float32) - np.array(compressed).astype(np.float32)
        ela = np.abs(ela)
        
        # Enhance for visualization
        ela = (ela - ela.min()) / (ela.max() - ela.min() + 1e-8)
        ela = (ela * 255).astype(np.uint8)
        
        # Convert to grayscale if RGB
        if len(ela.shape) == 3:
            ela = cv2.cvtColor(ela, cv2.COLOR_RGB2GRAY)
        
        return ela
    
    def get_image_metadata(self, file_storage):
        """
        Extract metadata from image
        
        Args:
            file_storage: Flask FileStorage object
            
        Returns:
            dict: Image metadata
        """
        image_bytes = file_storage.read()
        file_storage.seek(0)  # Reset file pointer
        
        image = Image.open(io.BytesIO(image_bytes))
        
        metadata = {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height,
            'file_size': len(image_bytes)
        }
        
        return metadata


# Utility functions
def create_gradient_background(width=1920, height=1080, colors=None):
    """
    Create AI-generated gradient background
    
    Args:
        width: Image width
        height: Image height
        colors: List of RGB color tuples for gradient
        
    Returns:
        numpy array: Gradient background image
    """
    if colors is None:
        # Default: Purple to blue gradient
        colors = [
            (138, 43, 226),   # Blue Violet
            (75, 0, 130),     # Indigo
            (25, 25, 112)     # Midnight Blue
        ]
    
    # Create gradient
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Vertical gradient
    for i in range(height):
        ratio = i / height
        
        # Interpolate between colors
        if ratio < 0.5:
            t = ratio * 2
            color = [
                int(colors[0][j] * (1-t) + colors[1][j] * t)
                for j in range(3)
            ]
        else:
            t = (ratio - 0.5) * 2
            color = [
                int(colors[1][j] * (1-t) + colors[2][j] * t)
                for j in range(3)
            ]
        
        gradient[i, :] = color
    
    # Add noise for texture
    noise = np.random.randint(-10, 10, (height, width, 3), dtype=np.int16)
    gradient = np.clip(gradient.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return gradient
