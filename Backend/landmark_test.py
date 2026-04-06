import cv2
import mediapipe as mp
mp_hands=mp.solutions.hands
hands=mp_hands.Hands(static_image_mode=True,max_num_hands=1,min_detection_confidence=0.5)

image = cv2.imread("test.jpg")
image_rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

results=hands.process(image_rgb)

if results.multi_hand_landmarks:
    hand_landmarks=results.multi_hand_landmarks[0]
    
    landmarks=[]
    for lm in hand_landmarks.landmark:
        landmarks.extend([lm.x,lm.y,lm.z])
    print("extracted landmark : ",landmarks[:6],"...")
    print("total length : ",len(landmarks))


mp_drawing = mp.solutions.drawing_utils
if results.multi_hand_landmarks:
    for hand_landmarks in results.multi_hand_landmarks:
        mp_drawing.draw_landmarks(image,hand_landmarks,mp_hands.HAND_CONNECTIONS)

cv2.imshow("hand landmarks : ",image)
cv2.waitKey(0)
cv2.destroyAllWindows()
hands.close()