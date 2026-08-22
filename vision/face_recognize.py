import numpy as np
import cv2  
import os
import pickle
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_DB = os.path.join(DATA_DIR, "face_database.pkl")

class FaceRecognizer:

    def __init__(self, database=DEFAULT_DB):
        self.database = database
        self.known_faces = self.load_database()

    def load_database(self):
        try:
            if os.path.exists(self.database):
                with open(self.database, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, list):
                        return data
            # Check legacy root path
            legacy_path = "face_database.pkl"
            if os.path.exists(legacy_path):
                with open(legacy_path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, list):
                        return data
            return []
        except Exception as e:
            print(f"Error loading database: {e}")
            return []

    def save_database(self, database):
        try:
            with open(self.database, "wb") as f:
                pickle.dump(database, f)
            self.known_faces = database  # Update local cache
            print(f"Database saved with {len(database)} entries.")
            return True
        except Exception as e:
            print(f"Error saving database: {e}")
            return False

    def get_available_camera(self):
        for index in [0, 1, -1]:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    return index
        return 0

    def capture_frame(self, window_name="Jarvis Face Capture"):
        camera_index = self.get_available_camera()
        cap = cv2.VideoCapture(camera_index)
        
        try:
            if not cap.isOpened():
                print("Could not open camera.")
                return None

            print("Press 's' to capture or 'q' to quit.")
            captured_frame = None
            
            start_time = time.time()
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                display_frame = frame.copy()
                cv2.putText(display_frame, "Position face and press 'S' to save", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(window_name, display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    captured_frame = frame
                    break
                elif key == ord('q') or (time.time() - start_time > 30): 
                    break
            return captured_frame
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def get_embedding(self, frame):
        try:
            from deepface import DeepFace
            results = DeepFace.represent(
                img_path=frame, 
                model_name="ArcFace",
                detector_backend="opencv",
                enforce_detection=True
            )
            
            try:
                import tensorflow as tf
                tf.keras.backend.clear_session()
            except:
                pass
            import gc
            gc.collect()

            if results and len(results) > 0:
                return results[0]["embedding"]
            return None
        except Exception as e:  
            print(f"Error extracting face embedding: {e}")
            return None

    def register_face(self, name, relation):
        print(f"Registering {name} ({relation})...")
        frame = self.capture_frame(f"Registering {name}")
        if frame is None:
            print("Capture failed.")
            return False

        embedding = self.get_embedding(frame)
        if embedding is None:
            print("Could not extract face embedding. Please try again.")
            return False

        database = self.load_database()
        
        database = [p for p in database if p['name'].lower() != name.lower()]
        
        database.append({
            "name": name,
            "relation": relation,
            "embedding": embedding,
            "timestamp": time.time()
        })

        return self.save_database(database)

    @staticmethod
    def register_person(name, relation, instance=None):
        if instance:
            return instance.register_face(name, relation)
        return FaceRecognizer().register_face(name, relation)

    def calculate_distance(self, emb1, emb2):
        emb1 = np.array(emb1)
        emb2 = np.array(emb2)
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    def recognize_face(self):
        print("Recognizing face...")
        frame = self.capture_frame("Recognizing Face")
        if frame is None:
            return None
        
        current_embedding = self.get_embedding(frame) 
        if current_embedding is None:
            return None
        
        database = self.load_database()
        if not database:
            print("Database is empty.")
            return None
        
        best_match = None
        max_similarity = -1

        for person in database:
            similarity = self.calculate_distance(current_embedding, person["embedding"])
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = person

        if max_similarity > 0.45:  
            return {
                "name": best_match["name"],
                "relation": best_match["relation"],
                "confidence": round(max_similarity * 100, 2)
            }
        
        print(f"No match found (Best similarity: {max_similarity:.2f})")
        return None
