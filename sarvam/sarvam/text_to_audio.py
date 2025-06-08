def text_to_speech(text,lang):
    import create_wav_file
    import requests
    import Sarvan_TTS
    audios = Sarvan_TTS.Text_to_audios(text,lang)
    #print(audios[:50])
    audio_file = create_wav_file.create_wav_file(audios)
    print("audio_file_path",audio_file)
    return audio_file

 