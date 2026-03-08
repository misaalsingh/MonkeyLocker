import cv2
import dlib
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import sqlite3
#for later use
class HandLandmarker:

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("Facial_Recognition/models/shape_predictor_68_face_landmarks.dat")
#Monkey_Locker_Cervesa/Facial_Recognition/models/shape_predictor_68_face_landmarks.dat
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