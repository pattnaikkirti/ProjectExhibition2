# ProjectExhibition2

# 🖐️ Hand Sign Detector

A real-time computer vision application that detects and classifies hand gestures using **MediaPipe** and **TensorFlow/Keras**. This project can be used for sign language recognition, touchless interfaces, or human-computer interaction.

---

## 🚀 Features
* **Real-time Detection:** High-speed hand landmark tracking using MediaPipe.
* **Custom Classification:** Deep Learning model trained to recognize specific hand signs (e.g., A-Z, 0-9, or custom gestures).
* **Visual Feedback:** On-screen overlays showing landmarks and predicted labels.
* **Robustness:** Works across various lighting conditions and backgrounds.

---

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Computer Vision:** OpenCV, MediaPipe
* **Deep Learning:** TensorFlow / Keras
* **Data Handling:** NumPy, Pandas

---

## 📂 Project Structure
```text
├── data/               # Captured images or processed landmarks
├── models/             # Pre-trained .h5 or .tflite models
├── src/
│   ├── collect_data.py # Script to capture hand signs via webcam
│   ├── train_model.py  # Script to train the neural network
│   └── main.py         # The real-time detection application
├── requirements.txt    # List of dependencies
└── README.md
