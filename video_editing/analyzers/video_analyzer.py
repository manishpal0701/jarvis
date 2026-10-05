
import os
import cv2
import subprocess
import json
import numpy as np

class VideoAnalyzer:
    def __init__(self):
        self.supported_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        self.gpu_device = None

    def _detect_gpu(self):
        try:
            if cv2.cuda.getDeviceCount() > 0:
                return "CUDA (OpenCV)"
        except:
            pass
        try:
            import tensorflow as tf
            if tf.config.list_physical_devices('GPU'):
                return "GPU (TensorFlow)"
        except:
            pass
        return "CPU"

    def analyze_folder(self, folder_path):
        from concurrent.futures import ThreadPoolExecutor
        
        files = [f for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in self.supported_extensions)]
        paths = [os.path.join(folder_path, f) for f in files]
        
        # Parallel Analysis for Production Speed
        print(f"Executing parallel analysis on {len(paths)} clips...")
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            raw_results = list(executor.map(self.analyze_clip, paths))
        
        # Filter high-quality assets
        results = [r for r in raw_results if r['quality_score'] > 0.4]
        return results

    def analyze_clip(self, file_path):
        metadata = self._get_metadata(file_path)
        cap = cv2.VideoCapture(file_path)
        frames = []
        try:
            # Sampling frames for analysis
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                for i in range(0, total_frames, max(1, total_frames // 10)):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
        finally:
            cap.release()

        # Compute specific metrics
        blur = self._check_blur(frames)
        motion = self._check_motion(file_path)
        brightness = self._check_lighting(frames)
        
        # Placeholder for more complex AI detection (Faces, Objects, Scenes)
        # In a production environment, we'd call Gemini or a local YOLO model here
        ai_data = self._ai_content_analysis(frames)

        quality_score = self._calculate_quality(blur, motion, brightness, ai_data)

        return {
            "path": file_path,
            "metadata": metadata,
            "metrics": {
                "blur": blur,
                "motion": motion,
                "brightness": brightness
            },
            "ai_data": ai_data,
            "quality_score": quality_score
        }

    def _get_metadata(self, path):
        # Using ffprobe for rich metadata
        try:
            cmd = f'ffprobe -v quiet -print_format json -show_format -show_streams "{path}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            return json.loads(result)
        except:
            return {}

    def _check_blur(self, frames):
        if not frames: return 0
        laplacians = [cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var() for f in frames]
        return np.mean(laplacians)

    def _check_lighting(self, frames):
        if not frames: return 0
        brightness = [np.mean(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)) for f in frames]
        return np.mean(brightness)

    def _check_motion(self, path):
        # Simplified motion detection using frame diff
        # In production, use optical flow
        return 0.5 # Placeholder

    def _ai_content_analysis(self, frames):
        """
        Uses Haar Cascades for real-time face detection.
        """
        if not frames: return {"faces": 0, "emotion": "neutral", "scene_type": "unknown"}
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        total_faces = 0
        
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            total_faces += len(faces)
            
        avg_faces = total_faces / len(frames)
        
        return {
            "faces": avg_faces,
            "emotion": "detecting...",
            "scene_type": "action" if avg_faces > 0.5 else "scenic"
        }

    def _calculate_quality(self, blur, motion, brightness, ai_data):
        score = 1.0
        if blur < 100: score -= 0.4 # Too blurry
        if brightness < 30 or brightness > 230: score -= 0.3 # Under/Overexposed
        return max(0, score)
