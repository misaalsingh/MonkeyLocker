import cv2
import dlib
import numpy as np
from deepface import DeepFace
from scipy.spatial.distance import cosine
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import sqlite3

''' functions needed basic shtuff
database operations
- save to blob
- return blob

facial embedding
- create facial embedding
- match face to existing embedding(give id)
- crop face from video

gesture embedding
- detect hand gesture
- draw hand landmarks

database operations
- save to blob
- insert to database
- replace blob in database
'''

class FaceMatch:

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("Facial_Recognition/models/shape_predictor_68_face_landmarks.dat")
    
    def get_aligned_face(self, predictor, frame, rect):
        shape = predictor(frame, rect)
        
        coords = np.array([[p.x, p.y] for p in shape.parts()])
        x_min = np.min(coords[:, 0])
        x_max = np.max(coords[:, 0])
        y_min = np.min(coords[:, 1])
        y_max = np.max(coords[:, 1])
        face_img = frame[y_min:y_max, x_min:x_max]
        face_img = cv2.resize(face_img, (160, 160))  
        return face_img
    
    def extract_embedding(self, face_img):
        result = DeepFace.represent(face_img, model_name="Facenet512", enforce_detection=False)
        return np.array(result[0]["embedding"], dtype=np.float64)
    
    def match_face(self, embedding, target_embedding):
        for username, stored_emb in target_embedding.items():
            dist = cosine(embedding, stored_emb)
            if dist < self.threshold:
                return username, dist
        return None, None
    
    def embedding_to_blob(self, embedding: np.ndarray) -> bytes:
        return embedding.tobytes()

    def blob_to_embedding(self, blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float64)

#for later use
class HandLandmarker:

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

        self.base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        self.hand_options = vision.HandLandmarkerOptions(
            base_options=self.base_options,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hand_detector = vision.HandLandmarker.create_from_options(self.hand_options)

    def draw_hand_landmarks(self, frame, hand_landmarks):
        """Draw hand landmarks on the frame"""
        h, w, _ = frame.shape
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (0, 17)  # Palm
        ]
        # Draw connections
        for connection in connections:
            start_idx, end_idx = connection
            start = hand_landmarks[start_idx]
            end = hand_landmarks[end_idx]
            
            start_point = (int(start.x * w), int(start.y * h))
            end_point = (int(end.x * w), int(end.y * h))
            
            cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        # Draw landmarks
        for landmark in hand_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)

    def detect_hand_gesture(self, hand_detector, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = hand_detector.detect(mp_image)
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                wrist = hand_landmarks[0] 
                index_tip = hand_landmarks[8] 
                if index_tip.y < wrist.y:
                    self.draw_hand_landmarks(frame, hand_landmarks)
                    return True
        return False

# example usage



# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     # Convert to grayscale for dlib detector
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = detector(gray)

#     for rect in faces:
#         # Align + crop face
#         face_img = get_aligned_face(frame, rect)
#         # Generate embedding
#         embedding = extract_embedding(face_img)
#         # Match face
#         username, dist = match_face(embedding, stored_embeddings)
#         if username:
#             cv2.putText(frame, f"{username} ({dist:.2f})", (rect.left(), rect.top() - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
#         else:
#             cv2.putText(frame, "Unknown", (rect.left(), rect.top() - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
#         # Draw rectangle around face
#         cv2.rectangle(frame, (rect.left(), rect.top()), (rect.right(), rect.bottom()), (255, 0, 0), 2)

#     # Gesture detection
#     hand_up = detect_hand_gesture(frame)
#     if hand_up:
#         cv2.putText(frame, "Hand Raised!", (50, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

#     cv2.imshow("Face+Gesture Login", frame)

#     key = cv2.waitKey(1) & 0xFF
#     if key == ord('q'):
#         break
#     elif key == ord('e'):
#         # Enrollment shortcut: press 'e' to store embedding
#         if faces:
#             face_img = get_aligned_face(frame, faces[0])
#             embedding = extract_embedding(face_img)
#             username = input("Enter username for enrollment: ")
#             stored_embeddings[username] = embedding
#             print(f"Stored embedding for {username}")

# cap.release()
# cv2.destroyAllWindows()