import os
from dotenv import load_dotenv

load_dotenv()
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import joblib
from collections import deque
import base64
import os
from google import genai
from google.genai import types
import pyttsx3
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

def generate():
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

# Create HandLandmarker
import os
model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

# Webcam
cap = cv2.VideoCapture(0)

window_size = 5
predictions_window = deque(maxlen=window_size)

recognized_text = ""
current_sign = ""
hand_present = False  

print("Press ESC to exit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) 
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    results = detector.detect(mp_image)

    if results.hand_landmarks:
        hand_present = True 

        for hand_landmarks in results.hand_landmarks:
            # Draw landmarks on frame
            for landmark in hand_landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            landmarks = []
            for lm in hand_landmarks:
                landmarks.extend([lm.x, lm.y, lm.z])

            pred = clf.predict([landmarks])[0]
            predictions_window.append(pred)

            smooth_pred = max(set(predictions_window), key=predictions_window.count)
            current_sign = encoder.inverse_transform([smooth_pred])[0]

            cv2.rectangle(frame, (40, 20), (400, 80), (0, 0, 0), -1)
            cv2.putText(frame, f"Current Sign: {current_sign}", (50, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    else:
        if hand_present and current_sign != "":
            recognized_text += current_sign
            current_sign = ""
        hand_present = False
        

    cv2.rectangle(frame, (40, 100), (800, 150), (0, 0, 0), -1)
    cv2.putText(frame, f"Text: {recognized_text}", (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)

    cv2.imshow("ISL Real-Time Recognition (String)", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

print("Final Recognized Text:", recognized_text)


if __name__ == "__main__":
    converted_text=generate()
    print(converted_text)
    speak(converted_text)
