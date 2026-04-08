const video = document.getElementById('webcam');
const canvasElement = document.getElementById('output_canvas');
const speakBtn = document.getElementById('speak-btn');
const currentStatementEl = document.getElementById('current-statement');

const textInput = document.getElementById('text-to-sign-input');
const translateBtn = document.getElementById('translate-btn');
const speakInputBtn = document.getElementById('speak-input-btn');
const signDisplay = document.getElementById('sign-display');


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

// Initialize environment on load
window.onload = () => {
    setupWebcam();
};