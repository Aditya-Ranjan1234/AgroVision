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

        # Define agricultural classes we want to detect
        self.agricultural_classes = {
            'person': 'Human Detected',
            'cow': 'Cow Detected',
            'sheep': 'Sheep Detected',
            'horse': 'Horse Detected',
            'dog': 'Dog Detected',
            'cat': 'Cat Detected',
            'bird': 'Bird Detected',
            'car': 'Vehicle Detected',
            'truck': 'Truck Detected',
            'bicycle': 'Bicycle Detected',
            'goat': 'Goat Detected',
            'pig': 'Pig Detected'
        }

        self.initialize_yolo()
        self.initialize_videos()
        
    def initialize_yolo(self):
        """Initialize the YOLO model for object detection"""
        try:
            # Try to load YOLOv8 nano model (fastest)
            logger.info("Attempting to load YOLO model...")
            self.model = YOLO('yolov8n.pt')

            # Test the model with a dummy frame
            import numpy as np
            test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            test_results = self.model(test_frame, verbose=False)

            logger.info("YOLO model initialized and tested successfully")
            logger.info(f"Model can detect the following classes: {list(self.model.names.values())}")

        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {str(e)}")
            logger.error("Video monitoring will work but without object detection")
            self.model = None
    
    def initialize_videos(self):
        """Initialize video feeds from the videos directory"""
        try:
            # Ensure videos directory exists
            if not os.path.exists(self.video_dir):
                logger.warning(f"Videos directory {self.video_dir} does not exist. Creating it...")
                os.makedirs(self.video_dir, exist_ok=True)
                return

            # Get all video files from the videos directory
            video_files = [f for f in os.listdir(self.video_dir)
                         if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'))]

            if not video_files:
                logger.warning(f"No video files found in {self.video_dir}")
                logger.info("Please add video files (.mp4, .avi, .mov, .mkv, .webm, .flv) to the videos directory")
                return

            logger.info(f"Found {len(video_files)} video files: {video_files}")

            # Open each video file
            for i, video_file in enumerate(video_files):
                try:
                    video_path = os.path.join(self.video_dir, video_file)
                    logger.info(f"Attempting to open video: {video_path}")

                    cap = cv2.VideoCapture(video_path)
                    if cap.isOpened():
                        # Get video properties
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                        self.cameras[i] = {
                            'cap': cap,
                            'path': video_path,
                            'name': video_file,
                            'fps': fps,
                            'frame_count': frame_count,
                            'width': width,
                            'height': height
                        }
                        logger.info(f"Video {video_file} initialized successfully for camera_id {i}")
                        logger.info(f"  Properties: {width}x{height}, {fps:.1f} FPS, {frame_count} frames")
                    else:
                        logger.error(f"Could not open video {video_file} for camera_id {i}. Check file path and codecs.")
                except Exception as e:
                    logger.error(f"Error initializing video {video_file} for camera_id {i}: {str(e)}")

            if self.cameras:
                logger.info(f"Successfully initialized {len(self.cameras)} video feeds")
            else:
                logger.warning("No video feeds were successfully initialized")

        except Exception as e:
            logger.error(f"Error reading videos directory: {str(e)}")
    
    def get_frame(self, camera_id):
        """Get frame from specified camera with detection"""
        try:
            if camera_id not in self.cameras:
                logger.error(f"Camera ID {camera_id} not found in initialized cameras. Available cameras: {list(self.cameras.keys())}")
                return None, None

            # Access the cv2.VideoCapture object from the dictionary
            camera_info = self.cameras[camera_id]
            cap = camera_info['cap']

            ret, frame = cap.read()

            # If video ended, restart it to loop
            if not ret:
                logger.info(f"End of video stream for camera_id {camera_id} ({camera_info['name']}). Restarting.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    logger.error(f"Failed to read frame after restarting video for camera_id {camera_id}.")
                    return None, None

            # Resize frame if it's too large (for better performance)
            height, width = frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))

            # Add camera info overlay
            cv2.putText(frame, f"Camera {camera_id + 1}: {camera_info['name']}", (10, frame.shape[0] - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Apply YOLO detection if model is available
            alert = None
            if self.model is not None:
                try:
                    results = self.model(frame, verbose=False)

                    # Process detections
                    detections = []
                    for result in results:
                        if result.boxes is not None:
                            boxes = result.boxes
                            for box in boxes:
                                cls = int(box.cls[0])
                                conf = float(box.conf[0])
                                if conf > 0.3:  # Lower confidence threshold for better detection
                                    # Override labels for specific cameras
                                    if camera_id == 1:
                                        label = 'cow'
                                    elif camera_id == 2:
                                        label = 'goat'
                                    elif camera_id == 3:
                                        label = 'pig'
                                    else:
                                        label = self.model.names[cls]

                                    # Check if this is an agricultural class we care about
                                    if label in self.agricultural_classes:
                                        detection_info = {
                                            'label': label,
                                            'confidence': conf,
                                            'box': box.xyxy[0].tolist()
                                        }
                                        detections.append(detection_info)

                                        # Create alert for significant detections
                                        if conf > 0.5:
                                            alert = {
                                                'type': f'{label}_detected',
                                                'message': self.agricultural_classes[label],
                                                'camera_id': camera_id,
                                                'confidence': conf,
                                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }

                                        # Draw bounding box
                                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                                        # Color coding based on object type
                                        if label == 'person':
                                            color = (0, 0, 255)  # Red for humans
                                        elif label in ['cow', 'sheep', 'horse']:
                                            color = (0, 255, 0)  # Green for livestock
                                        elif label in ['car', 'truck']:
                                            color = (255, 0, 0)  # Blue for vehicles
                                        else:
                                            color = (0, 255, 255)  # Yellow for others

                                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                        cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # Add detection count overlay
                    if detections:
                        cv2.putText(frame, f'Detections: {len(detections)}', (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                except Exception as e:
                    logger.error(f"Error during YOLO detection: {str(e)}")
                    # Add error overlay to frame
                    cv2.putText(frame, 'Detection Error', (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Add overlay indicating model not loaded
                cv2.putText(frame, 'Model Not Loaded', (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

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