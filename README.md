
Built by https://www.blackbox.ai

---

```markdown
# Attendance System with Face Recognition

## Project Overview
This project is a web-based attendance system that utilizes face recognition technology for user authentication and attendance recording. Built with Flask, it allows users to register, log in using their faces, and track their attendance (check-in/check-out). The application provides a user-friendly interface and is designed to manage attendance effectively.

## Installation

To set up the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   Ensure you have Python 3.6 or higher and pip installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download necessary models:**
   Run the following command to download the required face recognition models:
   ```bash
   python download_models.py
   ```

5. **Initialize the database:**
   The application uses SQLite, and the database will be initialized upon running the app for the first time.

## Usage

1. **Run the application:**
   ```bash
   python app.py
   ```
   The application will start on `http://127.0.0.1:8000`.

2. **Interact with the application:**
   - Navigate to the home page to register or log in.
   - For new users, complete the registration form, including uploading a face image.
   - Once registered, you can log in with your face image.
   - After logging in, users can check their attendance status and mark check-ins and check-outs.

## Features
- User registration with face image upload.
- Secure login using face recognition.
- Attendance tracking (check-in and check-out).
- User-specific attendance history access.
- Face recognition model downloading and setup.

## Dependencies
The project uses the following key dependencies (found in `requirements.txt`):
- Flask
- face_recognition
- Pillow
- numpy
- sqlite3 (built-in with Python, no installation required)

Make sure to have the necessary libraries installed to ensure the application runs smoothly.

## Project Structure
```
.
├── app.py                       # Main application file
├── database.py                  # Database interaction layer
├── download_models.py           # Script for downloading face recognition models
├── face_recognition_handler.py   # Handles face recognition logic
├── requirements.txt             # List of dependencies
└── static
    └── models                   # Directory for storing downloaded models
```

## Note
Ensure your camera is enabled on the device where you are testing the application for face recognition functionalities to work as intended.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
```