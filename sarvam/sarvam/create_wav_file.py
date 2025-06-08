import base64
import os
from datetime import datetime

def create_wav_file(base64_string, folder_path="audio_files"):
    import base64
    import os
    from datetime import datetime
    """
    Create a WAV file from base64 string with unique name
    
    Args:
        base64_string (str): Base64 encoded WAV data
        folder_path (str): Folder to save the WAV file
    
    Returns:
        str: Full path to the created WAV file
    """
    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"audio_{timestamp}.wav"
    file_path = os.path.join(folder_path, filename)
    
    # Decode base64 and write to file
    wav_data = base64.b64decode(base64_string)
    with open(file_path, "wb") as f:
        f.write(wav_data)
    
    return file_path

# Example usage
if __name__ == "__main__":
    # Replace with your actual base64 string
    base64_audio = "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmgfCCuBzvLZiTYIG2m98NiOOQoUYrjt559NEAxPqOPwtmMcBziN2fLNeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmgfCCmCzvLZiTYIG2m88NiOOQoUYrfp66hVFApHn+DyvmgfCCmCzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCmBzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCmBzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCmBzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCmBzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCmBzvLZiTYIG2m78NiOOQoUYrfp66hVFApHn+DyvmgfCCdw="
    
    # Create WAV file
    file_path = create_wav_file(base64_audio)
    print(f"WAV file created: {file_path}")