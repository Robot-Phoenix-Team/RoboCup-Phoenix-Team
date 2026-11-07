from ultralytics import YOLO
import cv2

# Chemin vers le modèle entraîné
model_path = 'best.pt'

# Charger le modèle entraîné
model = YOLO(model_path)

# Ouvrir la webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    results = model(frame)
    annotated_frame = results[0].plot()
    cv2.imshow('YOLOv8 Webcam Detection', annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
