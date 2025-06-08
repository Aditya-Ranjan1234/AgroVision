import cv2
import numpy as np
import time
from datetime import datetime
import os
import logging
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraHandler:
    def __init__(self):
        """Initialize the camera handler with YOLO model and video feeds"""
        self.cameras = {}
        self.model = None
        self.video_dir = os.path.join('static', 'videos')
        self.initialize_yolo()
        self.initialize_videos()
        
    def initialize_yolo(self):
        """Initialize the YOLO model for object detection"""
        try:
            self.model = YOLO('yolov8n.pt')
            logger.info("YOLO model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {str(e)}")
            self.model = None
    
    def initialize_videos(self):
        """Initialize video feeds from the videos directory"""
        try:
            # Get all video files from the videos directory
            video_files = [f for f in os.listdir(self.video_dir) 
                         if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
            
            if not video_files:
                logger.warning("No video files found in the videos directory")
                return
            
            # Open each video file
            for i, video_file in enumerate(video_files):
                try:
                    video_path = os.path.join(self.video_dir, video_file)
                    logger.info(f"Attempting to open video: {video_path}")
                    cap = cv2.VideoCapture(video_path)
                    if cap.isOpened():
                        self.cameras[i] = {
                            'cap': cap,
                            'path': video_path
                        }
                        logger.info(f"Video {video_file} initialized successfully for camera_id {i}")
                    else:
                        logger.error(f"Could not open video {video_file} for camera_id {i}. Check file path and codecs.")
                except Exception as e:
                    logger.error(f"Error initializing video {video_file} for camera_id {i}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error reading videos directory: {str(e)}")
    
    def get_frame(self, camera_id):
        """Get frame from specified camera with detection"""
        try:
            if camera_id not in self.cameras:
                logger.error(f"Camera ID {camera_id} not found in initialized cameras")
                return None, None

            # Access the cv2.VideoCapture object from the dictionary
            cap = self.cameras[camera_id]['cap']
            ret, frame = cap.read()

            # If video ended, restart it to loop
            if not ret:
                logger.info(f"End of video stream for camera_id {camera_id}. Restarting.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    logger.error(f"Failed to read frame after restarting video for camera_id {camera_id}.")
                    return None, None

            # Apply YOLO detection
            results = self.model(frame, verbose=False)
            
            # Process detections
            alert = None
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if conf > 0.5:  # Confidence threshold
                        label = self.model.names[cls]
                        if label == 'person':
                            alert = {
                                'type': 'human_detected',
                                'camera_id': camera_id,
                                'confidence': conf,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            # Draw bounding box
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                return None, None

            return buffer.tobytes(), alert

        except Exception as e:
            logger.error(f"Error getting frame from camera {camera_id}: {str(e)}")
            return None, None
    
    def release(self):
        """Release all video resources"""
        for camera_id, camera in self.cameras.items():
            try:
                camera['cap'].release()
                logger.info(f"Released video {camera['path']}")
            except Exception as e:
                logger.error(f"Error releasing video {camera['path']}: {str(e)}")
        
        self.cameras.clear() 