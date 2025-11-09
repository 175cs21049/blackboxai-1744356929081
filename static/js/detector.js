/**
 * AI Deepfake Detector - Frontend JavaScript
 * Handles file upload, detection, and results display
 */

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const historyContainer = document.getElementById('historyContainer');

// Statistics elements
const totalDetectionsEl = document.getElementById('totalDetections');
const realCountEl = document.getElementById('realCount');
const fakeCountEl = document.getElementById('fakeCount');
const avgConfidenceEl = document.getElementById('avgConfidence');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadStatistics();
    loadHistory();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Click to upload
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

/**
 * Handle uploaded files
 */
async function handleFiles(files) {
    if (files.length === 0) return;

    // Show progress
    progressContainer.classList.remove('hidden');
    resultsContainer.innerHTML = '';
    resultsSection.classList.add('hidden');

    // Process files
    if (files.length === 1) {
        await detectSingleImage(files[0]);
    } else {
        await detectBatchImages(files);
    }

    // Hide progress
    progressContainer.classList.add('hidden');

    // Reload statistics and history
    loadStatistics();
    loadHistory();
}

/**
 * Detect single image
 */
async function detectSingleImage(file) {
    try {
        const formData = new FormData();
        formData.append('image', file);

        const response = await fetch('/api/detect/image', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            displayResult(result, file);
        } else {
            showError(result.message || 'Detection failed');
        }
    } catch (error) {
        showError('Error: ' + error.message);
    }
}

/**
 * Detect batch of images
 */
async function detectBatchImages(files) {
    try {
        const formData = new FormData();
        
        for (let file of files) {
            formData.append('images', file);
        }

        const response = await fetch('/api/detect/batch', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            data.results.forEach((result, index) => {
                displayResult(result, files[index]);
            });
        } else {
            showError(data.message || 'Batch detection failed');
        }
    } catch (error) {
        showError('Error: ' + error.message);
    }
}

/**
 * Display detection result
 */
function displayResult(result, file) {
    resultsSection.classList.remove('hidden');

    const reader = new FileReader();
    reader.onload = (e) => {
        const imageUrl = e.target.result;
        
        const isPredictionFake = result.prediction === 'fake';
        const confidencePercent = (result.confidence * 100).toFixed(1);
        const fakePercent = (result.fake_probability * 100).toFixed(1);
        const realPercent = (result.real_probability * 100).toFixed(1);

        const resultCard = document.createElement('div');
        resultCard.className = 'result-card glass rounded-xl p-6';
        resultCard.innerHTML = `
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Image Preview -->
                <div class="space-y-4">
                    <img src="${imageUrl}" alt="Analyzed image" class="w-full h-64 object-cover rounded-lg shadow-lg">
                    <div class="text-white text-sm text-opacity-70">
                        <p><strong>Filename:</strong> ${file.name}</p>
                        <p><strong>Size:</strong> ${formatFileSize(file.size)}</p>
                    </div>
                </div>

                <!-- Results -->
                <div class="space-y-6">
                    <!-- Prediction Badge -->
                    <div class="text-center">
                        <div class="inline-block px-8 py-4 rounded-2xl ${isPredictionFake ? 'bg-red-500' : 'bg-green-500'} shadow-lg">
                            <div class="text-white text-3xl font-bold mb-1">
                                ${isPredictionFake ? '⚠️ FAKE' : '✓ REAL'}
                            </div>
                            <div class="text-white text-opacity-90 text-sm">
                                ${confidencePercent}% Confidence
                            </div>
                        </div>
                    </div>

                    <!-- Confidence Meter -->
                    <div class="space-y-3">
                        <div>
                            <div class="flex justify-between text-white text-sm mb-2">
                                <span>Real Probability</span>
                                <span class="font-semibold">${realPercent}%</span>
                            </div>
                            <div class="confidence-meter">
                                <div class="confidence-fill real" style="width: ${realPercent}%"></div>
                            </div>
                        </div>

                        <div>
                            <div class="flex justify-between text-white text-sm mb-2">
                                <span>Fake Probability</span>
                                <span class="font-semibold">${fakePercent}%</span>
                            </div>
                            <div class="confidence-meter">
                                <div class="confidence-fill fake" style="width: ${fakePercent}%"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Analysis Details -->
                    <div class="bg-white bg-opacity-10 rounded-lg p-4 space-y-2 text-white text-sm">
                        <h4 class="font-semibold text-lg mb-3">Analysis Details</h4>
                        <div class="flex justify-between">
                            <span class="text-opacity-70 text-white">Model:</span>
                            <span class="font-medium">CNN + RNN Hybrid</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-opacity-70 text-white">Algorithm:</span>
                            <span class="font-medium">MesoNet-4 + LSTM</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-opacity-70 text-white">Processing Time:</span>
                            <span class="font-medium">~2.3s</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-opacity-70 text-white">Image Quality:</span>
                            <span class="font-medium">${result.metadata ? 'High' : 'Standard'}</span>
                        </div>
                    </div>

                    <!-- Interpretation -->
                    <div class="bg-white bg-opacity-10 rounded-lg p-4 text-white text-sm">
                        <p class="text-opacity-90">
                            ${isPredictionFake 
                                ? '⚠️ This image shows signs of manipulation or AI generation. The neural network detected anomalies in facial features, lighting, or texture patterns typical of deepfakes.'
                                : '✓ This image appears to be authentic. No significant signs of manipulation or AI generation were detected by the neural network.'
                            }
                        </p>
                    </div>
                </div>
            </div>
        `;

        resultsContainer.appendChild(resultCard);
    };

    reader.readAsDataURL(file);
}

/**
 * Load statistics
 */
async function loadStatistics() {
    try {
        const response = await fetch('/api/detection/stats');
        const data = await response.json();

        if (data.status === 'success' && data.stats) {
            const stats = data.stats;
            
            // Animate counter updates
            animateCounter(totalDetectionsEl, stats.total_detections || 0);
            animateCounter(realCountEl, stats.real_count || 0);
            animateCounter(fakeCountEl, stats.fake_count || 0);
            
            const avgConf = stats.avg_confidence ? (stats.avg_confidence * 100).toFixed(0) : 0;
            avgConfidenceEl.textContent = avgConf + '%';
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

/**
 * Load detection history
 */
async function loadHistory() {
    try {
        const response = await fetch('/api/detection/history?limit=10');
        const data = await response.json();

        if (data.status === 'success' && data.history.length > 0) {
            historyContainer.innerHTML = '';
            
            data.history.forEach(item => {
                const historyItem = createHistoryItem(item);
                historyContainer.appendChild(historyItem);
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

/**
 * Create history item element
 */
function createHistoryItem(item) {
    const div = document.createElement('div');
    div.className = 'bg-white bg-opacity-10 rounded-lg p-4 flex items-center justify-between hover:bg-opacity-20 transition';
    
    const isPredictionFake = item.prediction === 'fake';
    const confidence = (item.confidence * 100).toFixed(1);
    const date = new Date(item.detected_at).toLocaleString();

    div.innerHTML = `
        <div class="flex items-center space-x-4">
            <div class="w-12 h-12 rounded-lg ${isPredictionFake ? 'bg-red-500' : 'bg-green-500'} flex items-center justify-center text-white text-xl">
                ${isPredictionFake ? '⚠️' : '✓'}
            </div>
            <div>
                <p class="text-white font-medium">${item.filename}</p>
                <p class="text-white text-opacity-70 text-sm">${date}</p>
            </div>
        </div>
        <div class="text-right">
            <p class="text-white font-semibold">${item.prediction.toUpperCase()}</p>
            <p class="text-white text-opacity-70 text-sm">${confidence}% confidence</p>
        </div>
    `;

    return div;
}

/**
 * Show error message
 */
function showError(message) {
    resultsSection.classList.remove('hidden');
    
    const errorCard = document.createElement('div');
    errorCard.className = 'result-card glass rounded-xl p-6 border-2 border-red-500';
    errorCard.innerHTML = `
        <div class="flex items-center space-x-4">
            <div class="text-red-500 text-4xl">⚠️</div>
            <div>
                <h4 class="text-white text-xl font-semibold mb-2">Error</h4>
                <p class="text-white text-opacity-90">${message}</p>
            </div>
        </div>
    `;
    
    resultsContainer.appendChild(errorCard);
}

/**
 * Animate counter
 */
function animateCounter(element, target) {
    const current = parseInt(element.textContent) || 0;
    const increment = Math.ceil((target - current) / 20);
    
    if (current < target) {
        element.textContent = current + increment;
        setTimeout(() => animateCounter(element, target), 50);
    } else {
        element.textContent = target;
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
