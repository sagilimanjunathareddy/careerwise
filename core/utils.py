

import requests
from django.conf import settings

def get_ai_career_guidance(skills, score):
    prompt = f"""
    A user has the following skills: {', '.join(skills)}.
    Their resume score is {score}/100.
    Based on these, suggest the top 2-3 suitable job roles and provide a personalized career guidance message.
    """

    headers = {
        "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "prompt": prompt,
        "max_tokens": 200,
        "temperature": 0.7,
        "top_p": 0.9
    }

    try:
        response = requests.post("https://api.together.xyz/v1/completions", headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['text'].strip()
        else:
            return f"API Error: {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"
