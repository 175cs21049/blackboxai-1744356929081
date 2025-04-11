import face_recognition
import numpy as np
from PIL import Image
import io
import base64
import json

class FaceRecognitionHandler:
    def __init__(self, tolerance=0.6):
        self.tolerance = tolerance

    def get_face_encoding(self, image_data):
        """
        Get face encoding from image data
        Args:
            image_data: bytes or base64 string of image
        Returns:
            dict: Status and face encoding if successful
        """
        try:
            # Convert image data to numpy array
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # Handle base64 image
                image_data = base64.b64decode(image_data.split(',')[1])
            
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)

            # Find face locations in the image
            face_locations = face_recognition.face_locations(image_np)

            if not face_locations:
                return {
                    "status": "error",
                    "message": "No face detected in the image"
                }

            if len(face_locations) > 1:
                return {
                    "status": "error",
                    "message": "Multiple faces detected. Please provide an image with a single face"
                }

            # Get face encoding
            face_encoding = face_recognition.face_encodings(image_np, face_locations)[0]

            return {
                "status": "success",
                "encoding": face_encoding.tolist()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing image: {str(e)}"
            }

    def verify_face(self, image_data, known_encodings):
        """
        Verify face against known encodings
        Args:
            image_data: bytes or base64 string of image to verify
            known_encodings: dict of user_id: encoding pairs
        Returns:
            dict: Status and user_id if match found
        """
        try:
            # Get encoding of the face to verify
            result = self.get_face_encoding(image_data)
            
            if result["status"] != "success":
                return result

            unknown_encoding = result["encoding"]

            # Convert known encodings to numpy arrays
            known_face_encodings = []
            user_ids = []
            
            for user_id, encoding in known_encodings.items():
                known_face_encodings.append(np.array(encoding))
                user_ids.append(user_id)

            if not known_face_encodings:
                return {
                    "status": "error",
                    "message": "No registered faces to compare against"
                }

            # Compare face against known encodings
            matches = face_recognition.compare_faces(
                known_face_encodings, 
                np.array(unknown_encoding),
                tolerance=self.tolerance
            )
            
            if True in matches:
                matched_index = matches.index(True)
                return {
                    "status": "success",
                    "user_id": user_ids[matched_index]
                }
            else:
                return {
                    "status": "error",
                    "message": "No matching face found"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during face verification: {str(e)}"
            }

    def compare_faces(self, face_encoding1, face_encoding2):
        """
        Compare two face encodings
        Args:
            face_encoding1: First face encoding
            face_encoding2: Second face encoding
        Returns:
            bool: True if faces match, False otherwise
        """
        try:
            # Convert encodings to numpy arrays if they're lists
            if isinstance(face_encoding1, list):
                face_encoding1 = np.array(face_encoding1)
            if isinstance(face_encoding2, list):
                face_encoding2 = np.array(face_encoding2)

            # Calculate face distance
            face_distance = face_recognition.face_distance([face_encoding1], face_encoding2)[0]
            
            # Return True if distance is below tolerance
            return face_distance <= self.tolerance

        except Exception as e:
            print(f"Error comparing faces: {str(e)}")
            return False

    def process_image_data(self, image_file):
        """
        Process image file from request
        Args:
            image_file: File object from request
        Returns:
            bytes: Image data
        """
        try:
            return image_file.read()
        except Exception as e:
            raise Exception(f"Error processing image file: {str(e)}")
