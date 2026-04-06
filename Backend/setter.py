import cv2
import os

folder = "a"
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(0)

count = 0
total_photos = 10   
capturing = False  

print("Press 't' to start capturing, 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  


    if capturing and count < total_photos:

        
        img_path = os.path.join(folder, f"im_{count+1}.jpg")

        cv2.imwrite(img_path, frame)
        count += 1

        cv2.waitKey(100)

    elif not capturing:
        cv2.putText(frame, "Press 't' to start capturing", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    
    cv2.imshow("Capture Photos", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('t'):
        capturing = True
        print("▶ Capturing started...")
    elif key == ord('q'):
        break

    if capturing and count >= total_photos:
        print(f"✅ {count} photos saved in '{folder}' folder.")
        break

cap.release()
cv2.destroyAllWindows()
