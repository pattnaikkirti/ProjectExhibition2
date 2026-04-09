const video = document.getElementById('webcam');
const canvasElement = document.getElementById('output_canvas');
const speakBtn = document.getElementById('speak-btn');
const clearBtn = document.getElementById('clear-btn');
const currentStatementEl = document.getElementById('current-statement');
const predictionStatusEl = document.getElementById('prediction-status');

const textInput = document.getElementById('text-to-sign-input');
const translateBtn = document.getElementById('translate-btn');
const speakInputBtn = document.getElementById('speak-input-btn');
const signDisplay = document.getElementById('sign-display');

const historyBox = document.getElementById('history-box');

// Prediction variables
let isPredicting = false;
let currentPrediction = '';
let recognizedText = '';
let lastPredictionTime = 0;
const PREDICTION_INTERVAL = 200; // Send frame every 200ms (5 FPS)

async function setupWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.addEventListener('loadeddata', () => {
            console.log("Webcam loaded successfully.");
            
        });
    } catch (error) {
        console.error("Error accessing webcam: ", error);
        alert("Please allow webcam access for the real-time detection to work.");
    }
}

function speakText(text) {
    if ('speechSynthesis' in window) {
        if (text === "Waiting for camera..." || text.trim() === "") return; 

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1; 
        utterance.pitch = 1; 
        window.speechSynthesis.speak(utterance);
    } else {
        alert("Your browser does not support Text-to-Speech.");
    }
}


speakBtn.addEventListener('click', () => {
    speakText(currentStatementEl.innerText);
});

clearBtn.addEventListener('click', () => {
    recognizedText = '';
    currentPrediction = '';
    updateCurrentStatement('Text cleared');
    updatePredictionStatus('');
    historyBox.innerHTML = '<span class="history-word">System</span><span class="history-word">Text cleared.</span>';
    
    // Clear canvas
    const canvas = canvasElement;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
});

speakInputBtn.addEventListener('click', () => {
    speakText(textInput.value);
});


const signEmojis = {
   'A': '✊', 'B': '✋', 'C': '🤌', 'D': '☝️', 'E': '🤜', 
    'F': '👌', 'G': '👈', 'H': '👉', 'I': '🤙', 'J': '⤴️',
    'K': '✌️', 'L': '🤟', 'M': '🖖', 'N': '🫰', 'O': '🤏', 
    'P': '📍', 'Q': '🫳', 'R': '🤞', 'S': '👊', 'T': '🤝',
    'U': '🤘', 'V': '🖖', 'W': '🖐️', 'X': '🙅', 'Y': '🤙', 'Z': '⚡'
  };

translateBtn.addEventListener('click', () => {
    const text = textInput.value.toUpperCase(); 
    signDisplay.innerHTML = ''; 

    if (!text) {
        signDisplay.innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Please enter text to compose.</span>';
        return;
    }

    for (let i = 0; i < text.length; i++) {
        const char = text[i];

        if (char === ' ') {
            const space = document.createElement('div');
            space.style.width = '30px'; 
            signDisplay.appendChild(space);
        } else if (char >= 'A' && char <= 'Z') {
            const charBox = document.createElement('div');
            charBox.className = 'sign-card';
            charBox.style.animationDelay = `${i * 0.05}s`;
            
            const emoji = signEmojis[char] || '🖐️';

            charBox.innerHTML = `
                <div class="sign-card-icon">${emoji}</div>
                <div class="sign-card-letter">${char}</div>
            `;
            
            signDisplay.appendChild(charBox);
        }
    }
});


textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') translateBtn.click();
});

// Frame capture and prediction functions
function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.8);
}

// Hand landmark drawing functions
function drawHandLandmarks(landmarks) {
    const canvas = canvasElement;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (!landmarks || landmarks.length === 0) {
        return;
    }
    
    // Draw connections
    drawConnections(ctx, landmarks);
    
    // Draw landmarks
    drawLandmarks(ctx, landmarks);
}

function drawLandmarks(ctx, landmarks) {
    landmarks.forEach(landmark => {
        const x = landmark.x * canvasElement.width;
        const y = landmark.y * canvasElement.height;
        
        // Draw larger, more visible dots with border
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, 2 * Math.PI);
        ctx.fillStyle = '#FF0000';  // Red filled circle
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, 2 * Math.PI);
        ctx.strokeStyle = '#FFFFFF';  // White border
        ctx.lineWidth = 2;
        ctx.stroke();
    });
}

function drawConnections(ctx, landmarks) {
    const connections = [
        [0, 1], [1, 2], [2, 3], [3, 4],  // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],  // Index finger
        [0, 9], [9, 10], [10, 11], [11, 12],  // Middle finger
        [0, 13], [13, 14], [14, 15], [15, 16],  // Ring finger
        [0, 17], [17, 18], [18, 19], [19, 20],  // Pinky
        [5, 9], [9, 13], [13, 17]  // Palm
    ];
    
    connections.forEach(connection => {
        const start = connection[0];
        const end = connection[1];
        if (start < landmarks.length && end < landmarks.length) {
            const startPoint = landmarks[start];
            const endPoint = landmarks[end];
            
            const x1 = startPoint.x * canvasElement.width;
            const y1 = startPoint.y * canvasElement.height;
            const x2 = endPoint.x * canvasElement.width;
            const y2 = endPoint.y * canvasElement.height;
            
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = '#FFFFFF';  // White lines
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    });
}

async function sendFrameForPrediction() {
    if (!isPredicting) return;
    
    try {
        const imageData = captureFrame();
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                handlePredictionResult(result);
            } else {
                console.error('Prediction failed:', result.error);
            }
        } else {
            console.error('Server error:', response.status);
        }
    } catch (error) {
        console.error('Error sending frame:', error);
    }
    
    // Use setTimeout instead of requestAnimationFrame for better control
    if (isPredicting) {
        setTimeout(sendFrameForPrediction, PREDICTION_INTERVAL);
    }
}

function handlePredictionResult(result) {
    if (result.hand_detected && result.prediction) {
        currentPrediction = result.prediction;
        updatePredictionStatus(currentPrediction);
        
        // Draw hand landmarks if available
        if (result.landmarks) {
            drawHandLandmarks(result.landmarks);
        }
        
        // Don't add to history yet, only show current prediction
    } else if (!result.hand_detected && currentPrediction) {
        // Clear canvas when no hand detected AND we had a current prediction
        const canvas = canvasElement;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Hand was removed, confirm the last prediction
        if (currentPrediction && currentPrediction !== '') {
            recognizedText += currentPrediction;
            updateRecognizedText();
            addToHistory(currentPrediction); // Add to history only when confirmed
        }
        currentPrediction = '';
        updatePredictionStatus('');
    }
}

function updatePredictionStatus(prediction) {
    if (prediction) {
        predictionStatusEl.innerHTML = `<span style="color: #4CAF50;">Detecting: ${prediction}</span>`;
    } else {
        predictionStatusEl.style.display = 'none';
    }
}

function updateCurrentStatement(text) {
    currentStatementEl.textContent = text || 'Waiting for sign...';
}

function updateRecognizedText() {
    if (recognizedText) {
        currentStatementEl.textContent = recognizedText;
        predictionStatusEl.innerHTML = `<span style="color: #2196F3;">Confirmed: ${recognizedText}</span>`;
        predictionStatusEl.style.display = 'block';
    }
}

function addToHistory(sign) {
    const signWord = document.createElement('span');
    signWord.className = 'history-word';
    signWord.textContent = sign;
    historyBox.appendChild(signWord);
    
    // Keep only last 20 signs in history
    while (historyBox.children.length > 20) {
        historyBox.removeChild(historyBox.firstChild);
    }
    
    // Scroll to bottom
    historyBox.scrollTop = historyBox.scrollHeight;
}

function startPrediction() {
    isPredicting = true;
    currentPrediction = '';
    recognizedText = '';
    lastPredictionTime = 0;
    updateCurrentStatement('Starting detection...');
    
    sendFrameForPrediction();
}

function stopPrediction() {
    isPredicting = false;
    updateCurrentStatement('Detection stopped');
}

// Initialize environment on load
window.onload = () => {
    setupWebcam().then(() => {
        // Start prediction after webcam is ready
        setTimeout(() => {
            startPrediction();
        }, 1000);
    });
};