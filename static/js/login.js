document.addEventListener('DOMContentLoaded', () => {
    let video = document.getElementById('video');
    let overlay = document.getElementById('overlay');
    let startButton = document.getElementById('startCamera');
    let loginButton = document.getElementById('loginButton');
    let statusDiv = document.getElementById('status');

    // Load face-api.js models
    Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
        faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
        faceapi.nets.faceRecognitionNet.loadFromUri('/static/models')
    ]).then(() => {
        startButton.disabled = false;
        statusDiv.textContent = 'Ready to start camera';
        statusDiv.className = 'text-center mb-6 text-sm text-green-600';

        // Check if running in a secure context
        if (!window.isSecureContext) {
            statusDiv.textContent = 'Camera access requires a secure (HTTPS) connection. Please use HTTPS or localhost.';
            statusDiv.className = 'text-center mb-6 text-sm text-yellow-600';
        }
    }).catch(err => {
        statusDiv.textContent = 'Error loading face recognition models: ' + err.message;
        statusDiv.className = 'text-center mb-6 text-sm text-red-600';
        console.error(err);
    });

    // Start camera when button is clicked
    startButton.addEventListener('click', async () => {
        try {
            statusDiv.textContent = 'Requesting camera access...';
            statusDiv.className = 'text-center mb-6 text-sm text-blue-600';
            
            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera access is not supported in this browser or environment. Please try using a different browser or device with camera support.');
            }

            // Check if running in a secure context
            if (!window.isSecureContext) {
                throw new Error('Camera access requires a secure (HTTPS) connection. Please use HTTPS or localhost.');
            }

            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                } 
            });
            
            video.srcObject = stream;
            await video.play();  // Ensure video starts playing
            
            startButton.disabled = true;
            loginButton.disabled = false;
            statusDiv.textContent = 'Camera started. Click "Login with Face" when ready';
            statusDiv.className = 'text-center mb-6 text-sm text-green-600';

            // Start face detection
            const canvas = faceapi.createCanvasFromMedia(video);
            overlay.appendChild(canvas);
            const displaySize = { width: video.width, height: video.height };
            faceapi.matchDimensions(canvas, displaySize);

            setInterval(async () => {
                try {
                    const detections = await faceapi.detectAllFaces(video, 
                        new faceapi.TinyFaceDetectorOptions())
                        .withFaceLandmarks()
                        .withFaceDescriptors();

                    const resizedDetections = faceapi.resizeResults(detections, displaySize);
                    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
                    faceapi.draw.drawDetections(canvas, resizedDetections);
                    faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

                    if (detections.length > 0) {
                        loginButton.disabled = false;
                        statusDiv.textContent = 'Face detected! You can now click "Login with Face"';
                        statusDiv.className = 'text-center mb-6 text-sm text-green-600';
                    } else {
                        loginButton.disabled = true;
                        statusDiv.textContent = 'No face detected. Please position your face in the camera';
                        statusDiv.className = 'text-center mb-6 text-sm text-yellow-600';
                    }
                } catch (err) {
                    console.error('Error during face detection:', err);
                    statusDiv.textContent = 'Error during face detection. Please try again.';
                    statusDiv.className = 'text-center mb-6 text-sm text-red-600';
                }
            }, 100);
        } catch (err) {
            console.error('Camera access error:', err);
            let errorMessage = 'Error accessing camera: ';
            
            if (err.name === 'NotAllowedError') {
                errorMessage += 'Camera access was denied. Please allow camera access and try again.';
            } else if (err.name === 'NotFoundError') {
                errorMessage += 'No camera found. Please ensure your camera is connected and try again.';
            } else if (err.name === 'NotReadableError') {
                errorMessage += 'Camera is in use by another application. Please close other applications and try again.';
            } else if (!window.isSecureContext) {
                errorMessage += 'Camera access requires a secure (HTTPS) connection. Please use HTTPS or localhost.';
            } else {
                errorMessage += err.message || 'Unknown error occurred';
            }
            
            statusDiv.textContent = errorMessage;
            statusDiv.className = 'text-center mb-6 text-sm text-red-600';
            startButton.disabled = false;
            loginButton.disabled = true;
        }
    });

    // Handle login button click
    loginButton.addEventListener('click', async () => {
        try {
            statusDiv.textContent = 'Processing...';
            statusDiv.className = 'text-center mb-6 text-sm text-blue-600';
            loginButton.disabled = true;

            // Capture current frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert to blob and send to server
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('face', blob);

                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        statusDiv.textContent = 'Login successful! Redirecting...';
                        statusDiv.className = 'text-center mb-6 text-sm text-green-600';
                        window.location.href = '/dashboard';
                    } else {
                        statusDiv.textContent = data.message || 'Login failed. Please try again.';
                        statusDiv.className = 'text-center mb-6 text-sm text-red-600';
                        loginButton.disabled = false;
                    }
                } catch (err) {
                    console.error('Login error:', err);
                    statusDiv.textContent = 'Error during login: ' + err.message;
                    statusDiv.className = 'text-center mb-6 text-sm text-red-600';
                    loginButton.disabled = false;
                }
            }, 'image/jpeg');

        } catch (err) {
            console.error('Error processing face:', err);
            statusDiv.textContent = 'Error processing face: ' + err.message;
            statusDiv.className = 'text-center mb-6 text-sm text-red-600';
            loginButton.disabled = false;
        }
    });

    // Stop camera when leaving page
    window.addEventListener('beforeunload', () => {
        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
    });
});
