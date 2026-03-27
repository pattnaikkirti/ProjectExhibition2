const video = document.getElementById('webcam');
const canvasElement = document.getElementById('output_canvas');
const speakBtn = document.getElementById('speak-btn');
const currentStatementEl = document.getElementById('current-statement');

// 1. Setup Webcam Feed
async function setupWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.addEventListener('loadeddata', () => {
            console.log("Webcam loaded successfully.");
            // predictWebcam(); // Uncomment when integrating MediaPipe
        });
    } catch (error) {
        console.error("Error accessing webcam: ", error);
        alert("Please allow webcam access for the real-time detection to work.");
    }
}

// 2. Setup Native Text-to-Speech (TTS)
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

// Initialize environment when the window loads
window.onload = () => {
    setupWebcam();
};