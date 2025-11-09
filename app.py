from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from database import Database
from face_recognition_handler import FaceRecognitionHandler
from models.deepfake_detector import DeepfakeDetector
from utils.image_processor import ImageProcessor
import os
from datetime import datetime
from functools import wraps
import numpy as np

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database and face recognition handler
db = Database()
face_handler = FaceRecognitionHandler()

# Initialize deepfake detector and image processor
print("Loading deepfake detection model...")
deepfake_detector = DeepfakeDetector()
image_processor = ImageProcessor()
print("Deepfake detector loaded successfully!")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/detector')
def detector():
    return render_template('detector.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        # Get form data
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        student_id = request.form.get('studentId')
        face_image = request.files.get('face')

        if not all([full_name, email, student_id, face_image]):
            return jsonify({
                "status": "error",
                "message": "All fields are required"
            })

        # Process face image
        image_data = face_handler.process_image_data(face_image)
        face_result = face_handler.get_face_encoding(image_data)

        if face_result["status"] != "success":
            return jsonify(face_result)

        # Register user in database
        result = db.register_user(
            full_name=full_name,
            email=email,
            student_id=student_id,
            face_encoding=face_result["encoding"]
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        if 'face' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No face image provided"
            })

        # Process face image
        face_image = request.files['face']
        image_data = face_handler.process_image_data(face_image)

        # Get all registered face encodings
        known_encodings = db.get_all_face_encodings()

        # Verify face
        result = face_handler.verify_face(image_data, known_encodings)

        if result["status"] == "success":
            # Set session
            session['user_id'] = result["user_id"]
            return jsonify({"status": "success"})
        
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/user')
@login_required
def get_user():
    try:
        user = db.get_user_by_id(session['user_id'])
        if user:
            # Remove sensitive data
            user.pop('face_encoding', None)
            return jsonify({
                "status": "success",
                "user": user
            })
        return jsonify({
            "status": "error",
            "message": "User not found"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/attendance/check-in', methods=['POST'])
@login_required
def check_in():
    try:
        result = db.mark_attendance(session['user_id'], 'check_in')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/attendance/check-out', methods=['POST'])
@login_required
def check_out():
    try:
        result = db.mark_attendance(session['user_id'], 'check_out')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/attendance/today')
@login_required
def get_today_attendance():
    try:
        attendance = db.get_today_attendance(session['user_id'])
        return jsonify({
            "status": "success",
            "attendance": attendance
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/attendance/history')
@login_required
def get_attendance_history():
    try:
        history = db.get_attendance_history(session['user_id'])
        return jsonify({
            "status": "success",
            "history": history
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

# Deepfake Detection API Endpoints

@app.route('/api/detect/image', methods=['POST'])
def detect_image():
    """Detect if a single image is deepfake or real"""
    try:
        if 'image' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No image file provided"
            })
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No image selected"
            })
        
        # Get image metadata
        metadata = image_processor.get_image_metadata(image_file)
        
        # Preprocess image
        processed_image = image_processor.preprocess_for_detection(image_file)
        
        # Detect deepfake
        result = deepfake_detector.predict(processed_image)
        
        # Save to database if user is logged in
        user_id = session.get('user_id', None)
        if user_id:
            db.save_detection_result(
                user_id=user_id,
                filename=image_file.filename,
                prediction_result=result,
                metadata=metadata
            )
        
        # Add metadata to result
        result['metadata'] = metadata
        result['status'] = 'success'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/detect/batch', methods=['POST'])
def detect_batch():
    """Detect multiple images at once"""
    try:
        if 'images' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No image files provided"
            })
        
        image_files = request.files.getlist('images')
        
        if len(image_files) == 0:
            return jsonify({
                "status": "error",
                "message": "No images selected"
            })
        
        results = []
        user_id = session.get('user_id', None)
        
        for image_file in image_files:
            try:
                # Get metadata
                metadata = image_processor.get_image_metadata(image_file)
                
                # Preprocess
                processed_image = image_processor.preprocess_for_detection(image_file)
                
                # Detect
                result = deepfake_detector.predict(processed_image)
                result['filename'] = image_file.filename
                result['metadata'] = metadata
                
                # Save to database
                if user_id:
                    db.save_detection_result(
                        user_id=user_id,
                        filename=image_file.filename,
                        prediction_result=result,
                        metadata=metadata
                    )
                
                results.append(result)
            
            except Exception as e:
                results.append({
                    'filename': image_file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/detection/history')
def get_detection_history():
    """Get detection history"""
    try:
        user_id = session.get('user_id', None)
        limit = request.args.get('limit', 50, type=int)
        
        history = db.get_detection_history(user_id=user_id, limit=limit)
        
        return jsonify({
            "status": "success",
            "history": history,
            "total": len(history)
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/detection/stats')
def get_detection_stats():
    """Get detection statistics"""
    try:
        user_id = session.get('user_id', None)
        
        stats = db.get_detection_stats(user_id=user_id)
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
