import os
from dotenv import load_dotenv

load_dotenv()
import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import deque
import base64
import io
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types
import pyttsx3
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def generate(recognized_text):
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Act as an expert English editor. I will provide you with a string of text that has no spaces and contains spelling errors. Your task is to parse this text and rewrite it as a perfectly grammatical, well-punctuated, and natural-sounding English statement."""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Defining the Task Scope**

I'm currently focused on defining the parameters of this English editing task. It's clear I need to receive a string lacking spaces and filled with errors. My primary goal will be to transform this into a flawless, natural-sounding English statement, paying close attention to punctuation and grammar. This initial stage involves understanding the specific scope of the challenge.


**Confirming Task Requirements**

I've clarified the core requirements for this English editing task. The goal is to receive an unspaced, error-ridden string and transform it into a flawless English sentence. I now understand that this involves comprehensive grammar, punctuation, and natural-sounding English. I'm ready to receive the input string and begin the editing process.


"""),
                types.Part.from_text(text="""Understood. I am ready. Please provide the string of text, and I will do my best to transform it into a perfectly grammatical, well-punctuated, and natural-sounding English statement."""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""howtogetprompttoconvertstatementwithoutspaces"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Decoding the Input**

I've been wrestling with this compact, space-less input. My focus is on unpacking its implied meaning and intentions.  It's a puzzle, but I'm getting closer to a reliable conversion. I'm prioritizing accuracy over speed, aiming to render a clear, understandable statement. The challenge lies in interpreting the user's intent within this condensed structure.


**Analyzing the String**

The user's request for space-less conversion is now clearer. I've broken down the input string into potential words. My linguistic analysis suggests a question about prompt functionality. Refining the construction to form a grammatically correct query is next. I am now working on the precise wording to achieve this conversion.


"""),
                types.Part.from_text(text="""How do you get a prompt to convert a statement without spaces?"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""hellothere
"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""Hello there."""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""mynamesayujya
"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""My name is Sayujya."""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""hixhowmaregfyou"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""Hi, how are you?"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=recognized_text),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        tools=tools,
    )


    corrected_text= ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        corrected_text+=chunk.text
        print(chunk.text, end="")
    print()
    return corrected_text.strip()

clf = joblib.load("isl_model.pkl")
encoder = joblib.load("isl_label_encoder.pkl")

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# Global state for simplicity (in production, use per-socket state)
clients = {}

@socketio.on('connect')
def handle_connect():
    clients[request.sid] = {
        'window_size': 5,
        'predictions_window': deque(maxlen=5),
        'recognized_text': "",
        'current_sign': "",
        'hand_present': False
    }
    print(f"Client {request.sid} connected")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in clients:
        del clients[request.sid]
    print(f"Client {request.sid} disconnected")

@socketio.on('frame')
def handle_frame(data):
    sid = request.sid
    if sid not in clients:
        return

    client = clients[sid]

    # Decode base64 image
    header, encoded = data.split(',', 1)
    img_data = base64.b64decode(encoded)
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return

    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    update = {
        'current_sign': client['current_sign'],
        'recognized_text': client['recognized_text'],
        'hand_present': client['hand_present']
    }

    if results.multi_hand_landmarks:
        client['hand_present'] = True

        for hand_landmarks in results.multi_hand_landmarks:
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])

            pred = clf.predict([landmarks])[0]
            client['predictions_window'].append(pred)

            smooth_pred = max(set(client['predictions_window']), key=client['predictions_window'].count)
            client['current_sign'] = encoder.inverse_transform([smooth_pred])[0]

            update['current_sign'] = client['current_sign']

    else:
        if client['hand_present'] and client['current_sign'] != "":
            client['recognized_text'] += client['current_sign']
            client['current_sign'] = ""
            update['recognized_text'] = client['recognized_text']
            update['current_sign'] = ""
        client['hand_present'] = False

    update['hand_present'] = client['hand_present']
    emit('update', update)

@socketio.on('finish')
def handle_finish():
    sid = request.sid
    if sid not in clients:
        return

    client = clients[sid]
    recognized_text = client['recognized_text']
    if recognized_text:
        converted_text = generate(recognized_text)
        emit('final', {'converted_text': converted_text})
        # Speak in a thread
        threading.Thread(target=speak, args=(converted_text,)).start()
    else:
        emit('final', {'converted_text': 'No text recognized'})

@app.route('/')
def index():
    return send_from_directory('../Frontend/Prototype2', 'index.html')

@app.route('/detect.html')
def detect():
    return send_from_directory('../Frontend/Prototype2', 'detect.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../Frontend/Prototype2', filename)
