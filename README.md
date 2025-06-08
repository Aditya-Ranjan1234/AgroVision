# Agriculture Vigilance System

A comprehensive farm monitoring and management system that helps farmers monitor their fields, get weather-based advice, detect plant diseases, and receive alerts for unauthorized access.

## Features

- **Weather Monitoring & Farm Advice**
  - Real-time weather data from OpenWeather API
  - AI-powered farming advice using Groq API
  - Location-based weather forecasts

- **Smart Camera Monitoring**
  - 4 camera feeds with YOLO object detection
  - Human detection and alert system
  - Real-time video streaming

- **Plant Disease & Pest Detection**
  - Upload images for disease detection
  - Uses trained model for accurate identification
  - Provides treatment recommendations

- **AI Chat Assistant**
  - Powered by Groq API
  - Answers farming-related questions
  - Provides real-time advice

- **Dashboard**
  - Real-time weather updates
  - Farm advice and alerts
  - Camera feed monitoring
  - Task management

## Prerequisites

- Python 3.8 or higher
- OpenWeather API key
- Groq API key
- YOLO model files

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Agriculture-Vigilance-System
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:
```
# Application Settings
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Weather API (OpenWeatherMap)
OPENWEATHER_API_KEY=your_openweather_api_key

# Groq AI API
GROQ_API_KEY=your_groq_api_key

# Model Configuration
YOLO_MODEL=yolov8n.pt
CONFIDENCE_THRESHOLD=0.5

# Alert Settings
ALERT_COOLDOWN=300  # 5 minutes in seconds

# Video Streams (Add your RTSP or video file paths here)
VIDEO_STREAMS=rtsp://example.com/stream1,rtsp://example.com/stream2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/agriculture_monitor.log
```

## Running the Application

1. Ensure your virtual environment is activated:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. Start the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **First Visit**
   - Enter your farm location when prompted
   - The system will fetch weather data and provide farming advice

2. **Dashboard**
   - View real-time weather and farming advice
   - Monitor camera feeds
   - Check alerts and tasks

3. **Camera Monitoring**
   - Access camera feeds at `/video`
   - Receive alerts for unauthorized access

4. **Disease Detection**
   - Upload plant images at `/disease`
   - Get instant disease identification and treatment advice

5. **Chat Assistant**
   - Click the chat icon in the bottom right
   - Ask farming-related questions
   - Get AI-powered responses

## Directory Structure

```
Agriculture-Vigilance-System/
├── app.py                 # Main Flask application
├── disease_detector.py    # Plant disease detection module
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
├── models/              # ML models
├── logs/                # Application logs
└── uploads/             # Uploaded images
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenWeather API for weather data
- Groq API for AI assistance
- YOLO for object detection
- Flask for web framework
