import os
import json
import logging
import requests
import base64
import groq
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, Response, g
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from disease_detector import DiseaseDetector
import time
from camera_handler import CameraHandler
from voice_handler import VoiceHandler
import atexit
from werkzeug.utils import secure_filename
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
app.config['SESSION_TYPE'] = 'filesystem'

# Enable CORS
CORS(app)

# Context processor to make global variables available to all templates
@app.context_processor
def inject_global_vars():
    return dict(translations=translations, g=g)

# Initialize SocketIO with reduced logging
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# Initialize Groq client
groq_client = groq.Client(api_key=os.getenv('GROQ_API_KEY'))

# Initialize Voice Handler globally
voice_handler = None
try:
    voice_handler = VoiceHandler()
    logger.info("Voice handler initialized successfully globally.")
except Exception as e:
    logger.error(f"Failed to initialize voice handler globally: {str(e)}")

# Initialize Disease Detector
try:
    disease_detector = DiseaseDetector(voice_handler=voice_handler)
    logger.info("Disease detector initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize disease detector: {str(e)}")
    disease_detector = None

# Initialize Camera Handler globally
camera_handler = None
try:
    camera_handler = CameraHandler()
    logger.info("Camera handler initialized successfully globally.")
except Exception as e:
    logger.error(f"Failed to initialize camera handler globally: {str(e)}")

# Register cleanup for camera handler
if camera_handler:
    atexit.register(lambda: camera_handler.release())
    logger.info("Camera handler release registered with atexit.")

# In-memory storage for alerts
alerts = []

# Video sources directory
VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')
os.makedirs(VIDEO_DIR, exist_ok=True)

# Weather cache
weather_cache = {
    'data': None,
    'last_updated': None,
    'cache_time': 3600  # 1 hour cache
}

# Hardcoded translations
translations = {
    'en': {
        'site_title': 'Agriculture Vigilance System',
        'home_link': 'Home',
        'video_monitoring_link': 'Video Monitoring',
        'disease_detection_link': 'Disease Detection',
        'location_weather_link': 'Location & Weather',
        'schemes_link': 'Agricultural Schemes',
        'chatbot_title': 'Agricultural Assistant Chat',
        'close_button': 'Close',
        'message_input_placeholder': 'Type your message...',
        'send_button': 'Send',
        'voice_input_button': 'Voice Input',
        'welcome_message': 'Welcome to the Agriculture Vigilance System',
        'welcome_description': 'Your comprehensive solution for modern agriculture management.',
        'get_started': 'Get Started',
        'current_location': 'Current Location',
        'weather_info': 'Weather Information',
        'loading_weather': 'Loading weather...',
        'location_error': 'Error getting location.',
        'weather_error': 'Error fetching weather data.',
        'upload_image_title': 'Upload Image for Disease Detection',
        'select_image': 'Select Image',
        'upload_button': 'Upload',
        'detection_results': 'Detection Results',
        'no_results': 'No disease detected or not a plant image.',
        'symptoms': 'Symptoms',
        'causes': 'Causes',
        'treatment_prevention': 'Treatment & Prevention',
        'no_feed': 'No camera feed available.',
        'alerts': 'Alerts',
        'no_alerts': 'No recent alerts.',
        'last_updated': 'Last Updated',
        'groq_error': 'AI advice unavailable.',
    },
    'hi': {
        'site_title': 'कृषि निगरानी प्रणाली',
        'home_link': 'मुख्य पृष्ठ',
        'video_monitoring_link': 'वीडियो निगरानी',
        'disease_detection_link': 'रोग पहचान',
        'location_weather_link': 'स्थान और मौसम',
        'schemes_link': 'कृषि योजनाएं',
        'chatbot_title': 'कृषि सहायक चैट',
        'close_button': 'बंद करें',
        'message_input_placeholder': 'अपना संदेश लिखें...',
        'send_button': 'भेजें',
        'voice_input_button': 'वॉइस इनपुट',
        'welcome_message': 'कृषि निगरानी प्रणाली में आपका स्वागत है',
        'welcome_description': 'आधुनिक कृषि प्रबंधन के लिए आपका व्यापक समाधान।',
        'get_started': 'शुरू करें',
        'current_location': 'वर्तमान स्थान',
        'weather_info': 'मौसम की जानकारी',
        'loading_weather': 'मौसम लोड हो रहा है...',
        'location_error': 'स्थान प्राप्त करने में त्रुटि।',
        'weather_error': 'मौसम डेटा प्राप्त करने में त्रुटि।',
        'upload_image_title': 'रोग पहचान के लिए छवि अपलोड करें',
        'select_image': 'छवि चुनें',
        'upload_button': 'अपलोड करें',
        'detection_results': 'पहचान के परिणाम',
        'no_results': 'कोई रोग नहीं पाया गया या यह पौधे की छवि नहीं है।',
        'symptoms': 'लक्षण',
        'causes': 'कारण',
        'treatment_prevention': 'उपचार और रोकथाम',
        'no_feed': 'कोई कैमरा फ़ीड उपलब्ध नहीं है।',
        'alerts': 'अलर्ट',
        'no_alerts': 'कोई हालिया अलर्ट नहीं।',
        'last_updated': 'अंतिम अपडेट',
        'groq_error': 'एआई सलाह अनुपलब्ध है।',
    },
    'ta': {
        'site_title': 'விவசாய கண்காணிப்பு அமைப்பு',
        'home_link': 'முகப்பு',
        'video_monitoring_link': 'வீடியோ கண்காணிப்பு',
        'disease_detection_link': 'நோய் கண்டறிதல்',
        'location_weather_link': 'இடம் மற்றும் வானிலை',
        'schemes_link': 'விவசாய திட்டங்கள்',
        'chatbot_title': 'விவசாய உதவி சாட்',
        'close_button': 'மூடு',
        'message_input_placeholder': 'உங்கள் செய்தியைத் தட்டச்சு செய்க...',
        'send_button': 'அனுப்பு',
        'voice_input_button': 'குரல் உள்ளீடு',
        'welcome_message': 'விவசாய கண்காணிப்பு அமைப்புக்கு வரவேற்கிறோம்',
        'welcome_description': 'நவீன விவசாய நிர்வாகத்திற்கான உங்கள் விரிவான தீர்வு.',
        'get_started': 'தொடங்கு',
        'current_location': 'தற்போதைய இடம்',
        'weather_info': 'வானிலை தகவல்',
        'loading_weather': 'வானிலை ஏற்றப்படுகிறது...',
        'location_error': 'இடத்தைப் பெறுவதில் பிழை.',
        'weather_error': 'வானிலை தரவைப் பெறுவதில் பிழை.',
        'upload_image_title': 'நோய் கண்டறிதலுக்கான படத்தை பதிவேற்றவும்',
        'select_image': 'படத்தைத் தேர்ந்தெடுக்கவும்',
        'upload_button': 'பதிவேற்று',
        'detection_results': 'கண்டறிதல் முடிவுகள்',
        'no_results': 'எந்த நோயும் கண்டறியப்படவில்லை அல்லது தாவர படம் இல்லை.',
        'symptoms': 'அறிகுறிகள்',
        'causes': 'காரணங்கள்',
        'treatment_prevention': 'சிகிச்சை மற்றும் தடுப்பு',
        'no_feed': 'கேமரா உணவு கிடைக்கவில்லை.',
        'alerts': 'எச்சரிக்கைகள்',
        'no_alerts': 'சமீபத்திய எச்சரிக்கைகள் இல்லை.',
        'last_updated': 'கடைசி புதுப்பிப்பு',
        'groq_error': 'AI ஆலோசனை கிடைக்கவில்லை.',
    },
    'te': {
        'site_title': 'వ్యవసాయ నిఘా వ్యవస్థ',
        'home_link': 'హోమ్',
        'video_monitoring_link': 'వీడియో పర్యవేక్షణ',
        'disease_detection_link': 'వ్యాధి నిర్ధారణ',
        'location_weather_link': 'స్థానం & వాతావరణం',
        'schemes_link': 'వ్యవసాయ పథకాలు',
        'chatbot_title': 'వ్యవసాయ సహాయ చాట్',
        'close_button': 'మూసివేయి',
        'message_input_placeholder': 'మీ సందేశాన్ని టైప్ చేయండి...',
        'send_button': 'పంపు',
        'voice_input_button': 'వాయిస్ ఇన్‌పుట్',
        'welcome_message': 'వ్యవసాయ నిఘా వ్యవస్థకు స్వాగతం',
        'welcome_description': 'ఆధునిక వ్యవసాయ నిర్వహణ కోసం మీ సమగ్ర పరిష్కారం.',
        'get_started': 'ప్రారంభించండి',
        'current_location': 'ప్రస్తుత స్థానం',
        'weather_info': 'వాతావరణ సమాచారం',
        'loading_weather': 'వాతావరణం లోడ్ అవుతೋంది...',
        'location_error': 'స్థానం పొందడంలో లోపం.',
        'weather_error': 'వాతావరణ డేటాను పొందడంలో లోపం.',
        'upload_image_title': 'వ్యాధి నిర్ధారణ కోసం చిత్రాన్ని అప్‌లోడ్ చేయండి',
        'select_image': 'చిత్రాన్ని ఎంచుకోండి',
        'upload_button': 'అప్‌లోడ్ చేయి',
        'detection_results': 'గుర్తింపు ఫలితాలు',
        'no_results': 'వ్యాధి కనుగొనబడలేదు లేదా మొక్కల చిత్రం కాదు.',
        'symptoms': 'లక్షణాలు',
        'causes': 'కారణాలు',
        'treatment_prevention': 'చికిత్స & నివారణ',
        'no_feed': 'కెమెరా ఫీడ్ అందుబాటులో లేదు.',
        'alerts': 'అలర్ట్‌లు',
        'no_alerts': 'ఇటీవలి అలర్ట్‌లు లేవు.',
        'last_updated': 'చివరిగా నవీకరించబడింది',
        'groq_error': 'AI సలహా అందుబాటులో లేదు.',
    },
    'kn': {
        'site_title': 'ಕೃಷಿ ಜಾಗೃತಿ ವ್ಯವಸ್ಥೆ',
        'home_link': 'ಮುಖಪುಟ',
        'video_monitoring_link': 'ವೀಡಿಯೊ ಮಾನಿಟರಿಂಗ್',
        'disease_detection_link': 'ರೋಗ ಪತ್ತೆ',
        'location_weather_link': 'ಸ್ಥಳ ಮತ್ತು ಹವಾಮಾನ',
        'schemes_link': 'ಕೃಷಿ ಯೋಜನೆಗಳು',
        'chatbot_title': 'ಕೃಷಿ ಸಹಾಯಕ ಚಾಟ್',
        'close_button': 'ಮುಚ್ಚಿ',
        'message_input_placeholder': 'ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ...',
        'send_button': 'ಕಳುಹಿಸು',
        'voice_input_button': 'ಧ್ವನಿ ಇನ್‌ಪುಟ್',
        'welcome_message': 'ಕೃಷಿ ಜಾಗೃತಿ ವ್ಯವಸ್ಥೆಗೆ ಸ್ವಾಗತ',
        'welcome_description': 'ಆಧುನಿಕ ಕೃಷಿ ನಿರ್ವಹಣೆಗಾಗಿ ನಿಮ್ಮ ಸಮಗ್ರ ಪರಿಹಾರ.',
        'get_started': 'ಪ್ರಾರಂಭಿಸಿ',
        'current_location': 'ಪ್ರಸ್ತುತ ಸ್ಥಳ',
        'weather_info': 'ಹವಾಮಾನ ಮಾಹಿತಿ',
        'loading_weather': 'ಹವಾಮಾನ ಲೋಡ್ ಆಗುತ್ತಿದೆ...',
        'location_error': 'ಸ್ಥಳವನ್ನು ಪಡೆಯುವಲ್ಲಿ ದೋಷ.',
        'weather_error': 'ಹವಾಮಾನ ಡೇಟಾವನ್ನು ಪಡೆಯುವಲ್ಲಿ ದೋಷ.',
        'upload_image_title': 'ರೋಗ ಪತ್ತೆಗಾಗಿ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
        'select_image': 'ಚಿತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ',
        'upload_button': 'ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
        'detection_results': 'ಗుರ్ತಿಸುವಿಕೆಯ ಫಲಿತಾಂಶಗಳು',
        'no_results': 'ಯಾವುದೇ ರೋಗ ಕಂಡುಬಂದಿಲ್ಲ ಅಥವಾ ಇದು ಸಸ್ಯದ ಚಿತ್ರವಲ್ಲ.',
        'symptoms': 'ಲಕ್ಷಣಗಳು',
        'causes': 'ಕಾರಣಗಳು',
        'treatment_prevention': 'ಚಿಕಿತ್ಸೆ ಮತ್ತು ತಡೆಗಟ್ಟುವಿಕೆ',
        'no_feed': 'ಯಾವುದೇ ಕ್ಯಾಮೆರಾ ಫೀಡ್ ಲಭ್ಯವಿಲ್ಲ.',
        'alerts': 'ಅಲರ్ಟ್‌ಗಳು',
        'no_alerts': 'ಯಾವುದೇ ಇತ್ತೀಚಿನ ಅಲರ్ಟ್‌ಗಳು ಇಲ್ಲ.',
        'last_updated': 'ಕೊನೆಯದಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ',
        'groq_error': 'AI ಸಲಹೆ ಲಭ್ಯವಿಲ್ಲ.',
    }
}

@app.before_request
def set_language():
    if 'lang' in request.args:
        g.lang = request.args['lang']
    elif 'lang' in session:
        g.lang = session['lang']
    else:
        g.lang = request.accept_languages.best_match(list(translations.keys())) or 'en'
    session['lang'] = g.lang

@app.route('/set_language/<lang_code>')
def set_language_route(lang_code):
    session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

@app.route('/api/location')
def api_location():
    """API endpoint to get user's location automatically using IP geolocation"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Location data received: {data}")
            return jsonify({
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'city': data['city'],
                'country': data['country_name']
            })
    except Exception as e:
        logger.error(f"Error getting location from IP: {str(e)}")
    
    # Fallback to default location
    return jsonify({
        'latitude': 20.5937,  # Default to India's center
        'longitude': 78.9629,
        'city': 'Default City',
        'country': 'India'
    })

@app.route('/location_weather_page')
def location_weather_page():
    """Render the location and weather page with dynamic data."""
    location = None
    weather_data = None
    groq_advice = None
    
    try:
        # Get location data (calling api_location to reuse its logic for IP-based location)
        location_response = api_location()
        if location_response.status_code == 200:
            location = json.loads(location_response.get_data(as_text=True))
            
            if location and location.get('latitude') and location.get('longitude'):
                lat = location['latitude']
                lon = location['longitude']
                
                # Get weather data
                weather_data = get_weather(lat, lon)
                
                # Get farming advice
                if weather_data:
                    # For get_groq_advice, we need to pass weather_data and location, and potentially g.lang.
                    # As get_groq_advice is a helper, we can call it directly.
                    groq_advice = get_groq_advice(weather_data, location)
                    
    except Exception as e:
        logger.error(f"Error fetching location, weather, or advice for location_weather_page: {e}")

    return render_template(
        'location_weather.html',
        location=location,
        weather_data=weather_data,
        groq_advice=groq_advice,
        translations=translations,
        g=g
    )

def get_weather(lat, lon):
    """Get weather data from OpenWeatherMap API"""
    current_time = time.time()
    if (weather_cache['data'] is not None and 
        weather_cache['last_updated'] is not None and
        (current_time - weather_cache['last_updated']) < weather_cache['cache_time']):
        return weather_cache['data']
    
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            logger.error("OpenWeather API key not found")
            return None
            
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            weather_data = {
                'temp': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
                'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
                'city': data.get('name', ''),
                'country': data['sys'].get('country', '')
            }
            weather_cache['data'] = weather_data
            weather_cache['last_updated'] = current_time
            logger.info(f"Weather data received: {weather_data}")
            return weather_data
        else:
            logger.error(f"Error response from OpenWeather: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return None

# Serve video files
@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files from the videos directory"""
    return send_from_directory(VIDEO_DIR, filename, as_attachment=False)

# API Endpoints
@app.route('/api/weather', methods=['POST'])
def api_weather():
    """Get weather data for given lat/lon"""
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    weather_data = get_weather(lat, lon)
    if weather_data is None:
        return jsonify({'error': 'Could not fetch weather data'}), 500
    return jsonify(weather_data)

@app.route('/api/advice', methods=['POST'])
def api_advice():
    data = request.get_json()
    weather_data = data.get('weather')
    location_data = data.get('location')
    lang_code = data.get('lang', 'en')

    if not weather_data or not location_data:
        return jsonify({'error': 'Weather and location data are required'}), 400

    # Temporarily set g.lang for get_groq_advice to use the requested language
    original_g_lang = getattr(g, 'lang', 'en') # Store original if exists
    g.lang = lang_code # Set g.lang for this request

    try:
        advice = get_groq_advice(weather_data, location_data)
        return jsonify({'advice': advice})
    except Exception as e:
        logger.error(f"Error in api_advice: {e}")
        return jsonify({'error': translations.get(lang_code, {}).get('groq_error', 'Could not fetch AI advice.')}), 500
    finally:
        # Restore original g.lang
        g.lang = original_g_lang

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    return jsonify(alerts[-10:])  # Return last 10 alerts

# Chat API
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    language = request.json.get('language', g.lang) # Get language from frontend, fallback to g.lang
    logger.info(f"Chat message received in {language}: {user_message}")

    def generate_groq_response(user_message):
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful agricultural assistant. Provide concise and accurate information about farming, crops, soil, pests, and diseases. Respond to the user's queries in a helpful and informative manner."
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )

            full_response_content = ""
            for chunk in chat_completion:
                if chunk.choices[0].delta.content:
                    full_response_content += chunk.choices[0].delta.content
            
            # Translate the Groq response if the user's language is not English
            target_lang = g.lang
            if target_lang != 'en' and voice_handler:
                try:
                    logger.info(f"Translating Groq response for chat from English to {target_lang}")
                    translated_response = voice_handler.translate_text(full_response_content, 'en', target_lang)
                    return translated_response
                except Exception as e:
                    logger.error(f"Error translating chat response: {e}")
                    return full_response_content # Return original if translation fails
            return full_response_content
        except Exception as e:
            logger.error(f"Error generating Groq response: {e}")
            return translations.get(g.lang, {}).get('groq_error', "I'm sorry, I couldn't process your request at the moment. Please try again later.")

    groq_response = generate_groq_response(user_message)
    return jsonify({'response': groq_response})

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text_route():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected audio file'}), 400

    try:
        audio_bytes = audio_file.read()
        logger.info(f"Received audio bytes length: {len(audio_bytes)}")
        
        # Determine source language from request or g.lang
        src_lang = request.form.get('lang', g.lang)
        logger.info(f"Performing speech-to-text with source language: {src_lang}")

        text_result = voice_handler.detect_and_translate(audio_bytes, src_lang, 'en') # Always translate to English for Groq input
        logger.info(f"Speech-to-text result (translated to English): {text_result}")
        return jsonify({'text': text_result})
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech_route():
    data = request.json
    text = data.get('text')
    target_lang = data.get('lang', g.lang) # Get target language from frontend or g.lang
    logger.info(f"Received text for speech-to-text: {text} for language {target_lang}")

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        audio_bytes = voice_handler.Text_to_audios(text, target_lang)
        if not audio_bytes:
            raise ValueError("Text_to_audios returned no audio bytes.")
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        logger.info(f"Generated text-to-speech audio with {len(audio_bytes)} bytes.")
        return jsonify({'audio': audio_base64})
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/suggestions', methods=['POST'])
def api_suggestions():
    user_input = request.json.get('input', '')
    logger.info(f"Received suggestion request: {user_input}")

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant providing 3-5 concise, comma-separated suggestions related to agriculture based on the user's input. The suggestions should be short phrases or keywords. For example, if the user input is 'crop', respond with 'Crop rotation, Soil health, Pest control, Fertilizers'. Do not include full sentences or conversational phrases. Only provide the suggestions separated by commas."
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            model="llama3-8b-8192", # Ensure this model is suitable for quick suggestions
            temperature=0.5,
            max_tokens=100,
            top_p=1,
            stop=None,
        )
        suggestions_text = chat_completion.choices[0].message.content.strip()
        suggestions_list = [s.strip() for s in suggestions_text.split(',') if s.strip()]
        logger.info(f"Groq suggestions: {suggestions_list}")
        
        # Translate suggestions if needed
        target_lang = g.lang
        if target_lang != 'en' and voice_handler:
            try:
                translated_suggestions = [voice_handler.translate_text(s, 'en', target_lang) for s in suggestions_list]
                return jsonify({'suggestions': translated_suggestions})
            except Exception as e:
                logger.error(f"Error translating suggestions: {e}")
                return jsonify({'suggestions': suggestions_list}) # Return original if translation fails
        
        return jsonify({'suggestions': suggestions_list})
    except Exception as e:
        logger.error(f"Error fetching suggestions from Groq: {e}")
        return jsonify({'suggestions': [translations.get(g.lang, {}).get('groq_error', 'AI advice unavailable.')]}), 500

# Routes
@app.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html', translations=translations, g=g)

def get_groq_advice(weather, location):
    logger.info(f"Attempting to get Groq advice for weather: {weather}, location: {location}")
    if not groq_client:
        logger.error("Groq client not initialized. Cannot get advice.")
        return translations.get(g.lang, {}).get('groq_error', 'AI advice unavailable.') # Use translation for error

    prompt = f"Given the current weather conditions in {location['city']}, {location['country']} (Weather: {weather['description']}, Temperature: {weather['temp']}°C, Humidity: {weather['humidity']}% , Wind Speed: {weather['wind_speed']} m/s) provide a concise agricultural advice or insight. Keep it brief and to the point. Consider general agricultural practices for the given weather. Be polite and helpful."

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an agricultural expert providing concise advice based on weather. Be helpful and informative."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=200,
            top_p=1,
            stop=None,
        )
        advice = chat_completion.choices[0].message.content
        logger.info(f"Groq advice received: {advice}")

        # Translate the Groq advice if the user's language is not English
        target_lang = g.lang
        if target_lang != 'en' and voice_handler:
            try:
                logger.info(f"Translating Groq advice from English to {target_lang}")
                translated_advice = voice_handler.translate_text(advice, 'en', target_lang)
                return translated_advice
            except Exception as e:
                logger.error(f"Error translating Groq advice: {e}")
                return advice # Return original if translation fails
        return advice
    except Exception as e:
        logger.error(f"Error fetching Groq advice: {e}")
        return translations.get(g.lang, {}).get('groq_error', 'Could not fetch AI advice.') # Use translation for error

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    """Stream video feed from specified camera"""
    # Use the globally initialized camera_handler
    global camera_handler 

    def generate(handler, cam_id):
        while True:
            if handler:
                frame, alert = handler.get_frame(cam_id)
                if frame:
                    # If there's an alert, add it to the global alerts list
                    if alert:
                        alerts.append(alert)
                        # Emit alert through Socket.IO
                        socketio.emit('new_alert', alert)
                    
                    # Yield the frame
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)  # Increased frame rate (was 0.1)
    
    return Response(generate(camera_handler, int(camera_id)),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video')
def video_monitoring():
    """Render the video monitoring page."""
    # Get list of video files from the static/videos directory
    video_files = []
    try:
        for f in os.listdir(VIDEO_DIR):
            if f.endswith(('.mp4', '.avi', '.mov')):
                video_files.append(f)
        logger.info(f"Found video files: {video_files}")
    except Exception as e:
        logger.error(f"Error listing video files: {e}")

    return render_template(
        'video.html',
        video_files=video_files,
        translations=translations,
        current_language=g.lang
    )

@app.route('/disease', methods=['GET', 'POST'])
def disease_detection():
    image_path = None
    disease_result = None
    pest_result = None
    error = None

    if request.method == 'POST':
        if 'file' not in request.files:
            error = translations.get(g.lang, {}).get('no_file_part_error', 'No file part')
        else:
            file = request.files['file']
            if file.filename == '':
                error = translations.get(g.lang, {}).get('no_selected_file_error', 'No selected file')
            elif file:
                # Ensure the uploads directory exists
                uploads_dir = os.path.join(app.static_folder, 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Sanitize filename and save securely
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                image_save_path = os.path.join(uploads_dir, unique_filename)
                file.save(image_save_path)
                logger.info(f"Image saved to: {image_save_path}")

                # Read the saved image into bytes for the disease detector
                with open(image_save_path, 'rb') as img_file:
                    image_bytes = img_file.read()

                # Construct web accessible path
                image_path = url_for('static', filename=f'uploads/{unique_filename}')

                if disease_detector:
                    detection_results = disease_detector.detect_disease(image_bytes, lang_code=g.lang) # Get separate results
                    if detection_results:
                        disease_result = detection_results.get('disease_result')
                        pest_result = detection_results.get('pest_result')
                        image_path = detection_results.get('image_path')
                    else:
                        error = translations.get(g.lang, {}).get('detection_failed_error', "Disease and pest detection failed.")
                else:
                    error = translations.get(g.lang, {}).get('disease_detector_not_initialized_error', "Disease detector not initialized.")
    else:
        # For GET requests, ensure results and image_path are reset or handled as empty
        pass # No change needed, already defaults to None

    return render_template('disease.html', image_path=image_path, disease_result=disease_result, pest_result=pest_result, error=error, translations=translations, g=g)

@app.route('/get_schemes_content')
def get_schemes_content():
    return render_template('schemes.html')

@app.route('/schemes')
def schemes():
    return render_template('schemes.html')

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.debug('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.debug('Client disconnected')

def geocode_location(location_name):
    geolocator = Nominatim(user_agent="agro_vigilance")
    try:
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
    return None, None, None

if __name__ == '__main__':
    try:
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs(VIDEO_DIR, exist_ok=True)
        
        # Start the application
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        # The camera handler is now managed globally via atexit.register
        pass # Removed g-based cleanup
