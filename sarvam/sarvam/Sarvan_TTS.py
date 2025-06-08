import requests
import logging

logger = logging.getLogger(__name__)

def Text_to_audios(text,lang):
    response = requests.post(
    "https://api.sarvam.ai/text-to-speech",
    headers={
        "api-subscription-key": "96e9ce28-c143-4dbd-aa30-704d9bc41de4"
    },
    json={
        "text": text,
        "target_language_code": lang
    },
    )
    #print("audios is ", response)
    #print("string is ",response.json()["audios"][:50])
    try:
        response_data = response.json()
        if "audios" in response_data and isinstance(response_data["audios"], list) and len(response_data["audios"]) > 0:
            return response_data["audios"][0]
        else:
            logger.error(f"Sarvam TTS response missing 'audios' key or empty: {response_data}")
            return None
    except ValueError: # Handles cases where response.json() might fail due to non-JSON response
        logger.error(f"Sarvam TTS response not valid JSON: {response.content}")
        return None
    except Exception as e:
        logger.error(f"Error processing Sarvam TTS response: {e}")
        return None
    