const video = document.getElementById('webcam');
const canvasElement = document.getElementById('output_canvas');
const speakBtn = document.getElementById('speak-btn');
const currentStatementEl = document.getElementById('current-statement');
const historyBox = document.getElementById('history-box');

// Include Socket.IO
const script = document.createElement('script');
script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js';
document.head.appendChild(script);

let socket;
let canvasCtx;

// 1. Setup Webcam Feed
async function setupWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.addEventListener('loadeddata', () => {
            console.log("Webcam loaded successfully.");
            canvasElement.width = video.videoWidth;
            canvasElement.height = video.videoHeight;
            canvasCtx = canvasElement.getContext('2d');
            startDetection();
        });
    } catch (error) {
        console.error("Error accessing webcam: ", error);
        alert("Please allow webcam access for the real-time detection to work.");
    }
}

// 2. Setup Socket.IO
function setupSocket() {
    socket = io('http://localhost:5000');

    socket.on('update', (data) => {
        // Update current sign
        // For now, just update the text
        currentStatementEl.innerText = data.recognized_text || "Waiting for input...";
        
        // Update history
        historyBox.innerHTML = '';
        if (data.recognized_text) {
            const words = data.recognized_text.split(''); // Assuming no spaces, each char is a word
            words.forEach(word => {
                const span = document.createElement('span');
                span.className = 'history-word';
                span.textContent = word;
                historyBox.appendChild(span);
            });
        } else {
            const span = document.createElement('span');
            span.className = 'history-word';
            span.textContent = 'Waiting for input...';
            historyBox.appendChild(span);
        }
    });

    socket.on('final', (data) => {
        currentStatementEl.innerText = data.converted_text;
        speakText(data.converted_text);
    });
}

// 3. Start Detection
function startDetection() {
    setInterval(() => {
        canvasCtx.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
        const frame = canvasElement.toDataURL('image/jpeg', 0.8);
        socket.emit('frame', frame);
    }, 100); // Send frame every 100ms
}

// 4. Setup Native Text-to-Speech (TTS)
function speakText(text) {
    if ('speechSynthesis' in window) {
        // Prevent empty strings from being spoken
        if (text === "Waiting for input..." || text.trim() === "") return; 

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1; // Adjust speaking speed (0.1 to 10)
        utterance.pitch = 1; // Adjust pitch (0 to 2)
        window.speechSynthesis.speak(utterance);
    } else {
        alert("Your browser does not support Text-to-Speech.");
    }
}

// Trigger speech when the button is clicked
speakBtn.addEventListener('click', () => {
    const textToSay = currentStatementEl.innerText;
    speakText(textToSay);
});

// Finish button or something, but for now, add a button to finish
const finishBtn = document.createElement('button');
finishBtn.textContent = 'Finish';
finishBtn.style.marginLeft = '10px';
document.querySelector('.statement-controls').appendChild(finishBtn);
finishBtn.addEventListener('click', () => {
    socket.emit('finish');
});

// Initialize environment when the window loads
window.onload = () => {
    script.onload = () => {
        setupSocket();
        setupWebcam();
    };
};