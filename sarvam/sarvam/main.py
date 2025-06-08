import sys
import audio_to_text
import text_to_audio
import groq

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_test.py <audio_file> [language_code]")
        print("Example: python simple_test.py audio.mp3 hi-IN")
        sys.exit(1)
    
    audio_file = sys.argv[1] # Your API key
    text,language_code,translated_text = audio_to_text.sarvam_api(audio_file)
    print("result")
    print("detected language:", language_code)
    print("speech to text",text)
    print("english text",translated_text)
    prompt = """You are an expert agricultural assistant who understands farmers’ concerns and crop-related problems and replies as a chat bot. so keep it short and crisp - up to the point, limit your respone to 300 characters, complete in one paragraphs.
Given the farmer’s text describing what crops they are planting, the issues they face, and any other relevant details, analyze the input carefully and provide a helpful, clear, and practical response.
Your response should include advice, possible causes of problems,simple solutions.Always be correct and blunt.empathetic and respectful to the farmer’s situation.here is the input:
"""+text
    #passing to groq
    answer = groq.groq_chat(prompt)
    print(answer)
    audio_file_path = text_to_audio.text_to_speech(answer,language_code)
    print(audio_file_path)
