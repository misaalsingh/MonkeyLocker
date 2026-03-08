from typing import Optional, Tuple, Dict
import numpy as np
import cv2
from scipy.spatial.distance import cosine
from Facial_Recognition import FaceMatch
from sqlalchemy.orm import Session
from models.users import User

class FaceRecognitionService:
    
    def __init__(self, match_threshold: float = 0.5):
        self.face_match = FaceMatch()

    def enroll_face(self, db: Session, user_id: int, image_bytes: bytes) -> Dict:
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image")
            embedding = self.face_match.extract_embedding(img)
        except ValueError as e:
            raise ValueError(f"Face extraction failed: {str(e)}")
        embedding_blob = self.face_match.embedding_to_blob(embedding)
        user.face_embedding = embedding_blob
        db.commit()
        db.refresh(user)
        return {
            "success": True,
            "message": f"Face enrolled for user {user_id}",
            "user_id": user_id
        }
    
    def authenticate_face(self, db: Session, image_bytes: bytes) -> Tuple[Optional[int], Optional[float]]:
        try:
            query_embedding = self.face_sdk.extract_embedding(image_bytes)
        except ValueError as e:
            raise ValueError(f"Face detection failed: {str(e)}")
        
        users_with_faces = db.query(User).filter(User.face_embedding.isnot(None)).all()
        
        if not users_with_faces:
            return None, None
        
        stored_embeddings = {}
        for user in users_with_faces:
            embedding = self.face_match.blob_to_embedding(user.face_embedding)
            stored_embeddings[user.id] = embedding
        
        user_id, confidence = self.face_sdk.find_best_match(query_embedding, stored_embeddings)
        return user_id, confidence
    
    def verify_face(self, db: Session, user_id: int, image_bytes: bytes) -> Tuple[bool, float]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.face_embedding:
            return False, 0.0
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return False, 0.0
            query_embedding = self.face_match.extract_embedding(img)
        except Exception:
            return False, 0.0
        stored_embedding = self.face_match.blob_to_embedding(user.face_embedding)
        distance = float(cosine(query_embedding, stored_embedding))
        confidence = round(1.0 - distance, 4)
        is_match = distance < self.face_match.threshold
        return is_match, confidence
    
    def remove_face_enrollment(self, db: Session, user_id: int) -> Dict:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"success": False, "message": f"User {user_id} not found"}
        
        if not user.face_embedding:
            return {"success": False, "message": f"User {user_id} has no enrolled face"}
        
        user.face_embedding = None
        db.commit()
        
        return {"success": True, "message": f"Face enrollment removed for user {user_id}"}
    
    def is_face_enrolled(self, db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        return user is not None and user.face_embedding is not None