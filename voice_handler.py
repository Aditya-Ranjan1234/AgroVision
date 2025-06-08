import os
import sys
import logging
from pathlib import Path
import base64
import uuid # For unique filenames

# Add the root project directory to Python path for package discovery
sarvam_root_path = Path("D:/My Projects/Agriculture Vigilance System")
sys.path.append(str(sarvam_root_path))

# Import the functions directly
from sarvam.sarvam.Sarvam_STT import detect_and_translate
from sarvam.sarvam.Sarvan_TTS import Text_to_audios

logger = logging.getLogger(__name__)

class VoiceHandler:
    def __init__(self):
        logger.info("Sarvam voice system handler initialized.")
        self.lang_map = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'kn': 'kn-IN'
            # Add other mappings if more languages are supported
        }

    def text_to_speech(self, text, lang="en"):
        """Convert text to speech using Sarvam TTS function"""
        sarvam_lang = self.lang_map.get(lang, 'en-IN') # Default to en-IN if not found
        try:
            audio_base64 = Text_to_audios(text, sarvam_lang)
            # Sarvam returns base64 encoded audio, decode it
            audio_bytes = base64.b64decode(audio_base64)
            return audio_bytes
        except Exception as e:
            logger.error(f"Error in text to speech with Sarvam: {str(e)}")
            return None

    def speech_to_text(self, audio_data, src_lang="en"):
        """Convert speech to text using Sarvam STT function"""
        sarvam_src_lang = self.lang_map.get(src_lang, 'en-IN') # Default to en-IN if not found
        # Save audio_data to a temporary WAV file
        temp_filename = f"temp_audio_{uuid.uuid4()}.wav"
        temp_filepath = os.path.join(os.getcwd(), temp_filename) # Save in current working directory
        
        try:
            with open(temp_filepath, 'wb') as f:
                f.write(audio_data)

            # Call Sarvam STT function
            # Assuming detect_and_translate can take src_lang and target_lang for translation
            # If it only does STT and not STT+Translation, this needs to be split.
            # For now, it will assume it tries to translate to English by default for Groq.
            response = detect_and_translate(temp_filepath, sarvam_src_lang, 'en-IN') 
            
            if response and 'text' in response:
                return response['text']
            elif response and 'detail' in response:
                logger.error(f"Sarvam STT API error: {response['detail']}")
                return "Sorry, I couldn't understand that. Please try again."
            else:
                logger.warning(f"Unexpected response from Sarvam STT: {response}")
                return "Sorry, I couldn't process your voice. Please try again."
        except Exception as e:
            logger.error(f"Error in speech to text with Sarvam: {str(e)}")
            return "Sorry, there was an error processing your voice input."
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                logger.info(f"Cleaned up temporary file: {temp_filepath}") 