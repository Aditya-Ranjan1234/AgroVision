import requests

def groq_chat(prompt):
    """
    Simple function to get response from Groq API
    
    Args:
        prompt (str): Your question/prompt
    
    Returns:
        str: The response text
    """
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer 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"
        },
        json={
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    
    return response.json()['choices'][0]['message']['content']

# Usage
if __name__ == "__main__":
    text = "I planted tomatoes and potatoes this season. But my tomato plants have yellow leaves and some bugs. Also, the soil seems dry even after watering."
    answer = groq_chat("""You are an expert agricultural assistant who understands farmers’ concerns and crop-related problems and replies as a chat bot. so keep it short and crisp - up to the point.
Given the farmer’s speech text describing what crops they are planting, the issues they face, and any other relevant details, analyze the input carefully and provide a helpful, clear, and practical response.
Your response should include advice, possible causes of problems, solutions, and any relevant recommendations related to planting, pest control, soil health, irrigation, weather, or farming practices.
Always be empathetic and respectful to the farmer’s situation.
                       here is the input:
"""+text)
    print(answer)