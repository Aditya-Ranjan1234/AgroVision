import sys
def sarvam_api(audio_file):
    import requests
    import sys
    import os
    import Sarvam_STT
    import Google_Translate
    results = Sarvam_STT.detect_and_translate(audio_file)
    text = results["transcript"]
    translated_text = None
    if not results["language_code"] == "en":
        translated_text = Google_Translate.detect_and_translate(text)
    else:
        translated_text = text
    return text,results["language_code"],translated_text
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_test.py <audio_file> [language_code]")
        print("Example: python simple_test.py audio.mp3 hi-IN")
        sys.exit(1)
    
    audio_file = sys.argv[1] # Your API key
    
    text,language_code,translated_text = sarvam_api(audio_file)
    print("result")
    print("detected language:", language_code)
    print("speech to text",text)
    print("english text",translated_text)