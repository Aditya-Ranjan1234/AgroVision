from pydub import AudioSegment
import sys
import os

def convert_mp3_to_wav(input_file):
    if not input_file.lower().endswith('.mp3'):
        print("❌ Please provide a .mp3 file.")
        return

    try:
        audio = AudioSegment.from_mp3(input_file)
        output_file = input_file.replace(".mp3", ".wav")
        audio.export(output_file, format="wav")
        print(f"✅ Conversion complete! Saved as: {output_file}")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mp3_to_wav.py yourfile.mp3")
    else:
        convert_mp3_to_wav(sys.argv[1])