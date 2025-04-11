let video = document.getElementById('video');
let overlay = document.getElementById('overlay');
let startButton = document.getElementById('startCamera');
let captureButton = document.getElementById('captureImage');
let registerButton = document.getElementById('registerButton');
let statusDiv = document.getElementById('status');
let registrationForm = document.getElementById('registrationForm');

let capturedImage = null;

// Load face-api.js models
Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
    faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
    faceapi.nets.faceRecognitionNet.loadFromUri('/static/models')
]).then(() => {
    startButton.disabled = false;
    statusDiv.textContent = 'Ready to start camera';
}).catch(err => {
    statusDiv.textContent = 'Error loading face recognition models';
    console.error(err);
});

// Start camera when button is clicked
startButton.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: {} });
        video.srcObject = stream;
        startButton.disabled = true;
        captureButton.disabled = false;
        statusDiv.textContent = 'Camera started. Position your face and click "Capture Image"';

        // Start face detection
        video.addEventListener('play', () => {
            const canvas = faceapi.createCanvasFromMedia(video);
            overlay.appendChild(canvas);
            const displaySize = { width: video.width, height: video.height };
            faceapi.matchDimensions(canvas, displaySize);

            setInterval(async () => {
                const detections = await faceapi.detectAllFaces(video, 
                    new faceapi.TinyFaceDetectorOptions())
                    .withFaceLandmarks();

                const resizedDetections = faceapi.resizeResults(detections, displaySize);
                canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
                faceapi.draw.drawDetections(canvas, resizedDetections);
                faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

                captureButton.disabled = detections.length !== 1;
            }, 100);
        });
    } catch (err) {
        statusDiv.textContent = 'Error accessing camera: ' + err.message;
        console.error(err);
    }
});

// Handle capture button click
captureButton.addEventListener('click', async () => {
    try {
        // Capture current frame
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        // Store the captured image
        canvas.toBlob((blob) => {
            capturedImage = blob;
            statusDiv.textContent = 'Image captured successfully! Fill in your details and click Register';
            registerButton.disabled = false;
        }, 'image/jpeg');

    } catch (err) {
        statusDiv.textContent = 'Error capturing image: ' + err.message;
        console.error(err);
    }
});

// Handle form submission
registrationForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!capturedImage) {
        statusDiv.textContent = 'Please capture your face image first';
        return;
    }

    const formData = new FormData();
    formData.append('face', capturedImage);
    formData.append('fullName', document.getElementById('fullName').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('employeeId', document.getElementById('employeeId').value);

    try {
        statusDiv.textContent = 'Registering...';
        registerButton.disabled = true;

        const response = await fetch('/api/register', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            statusDiv.textContent = 'Registration successful! Redirecting to login...';
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            statusDiv.textContent = data.message || 'Registration failed. Please try again.';
            registerButton.disabled = false;
        }
    } catch (err) {
        statusDiv.textContent = 'Error during registration: ' + err.message;
        registerButton.disabled = false;
        console.error(err);
    }
});

// Stop camera when leaving page
window.addEventListener('beforeunload', () => {
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
});
