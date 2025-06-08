def Text_to_audios(text,lang):
    import requests
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
    return response.json()["audios"][0]
    