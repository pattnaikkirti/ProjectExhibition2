import cv2
import mediapipe as mp
import os
import numpy as np 
import pandas as pd
mp_hands =mp.solutions.hands
hands=mp_hands.Hands(static_image_mode=True,max_num_hands=1,min_detection_confidence=0.5)

dataset_path = "ISL_Dataset"
data =[]
lables=[]

for label in os.listdir(dataset_path):
    class_dir = os.path.join(dataset_path,label)
    if not os.path.isdir(class_dir):
        continue
    print(f"processing : {label}")
    for img_name in os.listdir(class_dir):
        img_path = os.path.join(class_dir,img_name)
        image =cv2.imread(img_path)

        if image is None:
            continue
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results= hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            landmarks=[]
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x,lm.y,lm.z])
            data.append(landmarks)
            lables.append(label)
hands.close()

df=pd.DataFrame(data)
df['label'] = lables

df.to_csv("isl_landmarks.csv", index=False)
print("Saved dataset with alphabet : ",df.shape)