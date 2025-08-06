import re
import pdfplumber
import json
import torch
from django.conf import settings

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from transformers import AutoModelForCausalLM, AutoTokenizer

from .models import UserProfile
from resume_parser.parser import parse_resume
from .job_api import fetch_jobs
import requests
from .utils import get_ai_career_guidance

# Regex patterns
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(\+91 9182919149 [\-\s]?)?[6789]\d{9}'
LINKEDIN_REGEX = r'(linkedin\.com/in/[a-zA-Z0-9_-]+)'
GITHUB_REGEX = r'(github\.com/[a-zA-Z0-9_-]+)'


def extract_text_from_pdf(path):
    text = ''
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text


def extract_data_from_text(text):
    email = re.findall(EMAIL_REGEX, text)
    phone = re.findall(PHONE_REGEX, text)
    linkedin = re.findall(LINKEDIN_REGEX, text)
    github = re.findall(GITHUB_REGEX, text)

    return {
        'email': email[0] if email else None,
        'phone': phone[0] if phone else None,
        'linkedin': linkedin[0] if linkedin else None,
        'github': f"https://{github[0]}" if github else None
    }


def calculate_resume_score(data):
    score = 0
    if data.get('email'): score += 20
    if data.get('phone'): score += 10
    if data.get('linkedin'): score += 10
    if data.get('github'): score += 10
    if data.get('skills'): score += min(len(data['skills']) * 3, 20)
    if data.get('experience'): score += 10
    if data.get('education'): score += 10
    return min(score, 100)


def get_recommendations(skills, score):
    recommendations = []
    
    if not skills:
        return ["No matching jobs found"], "Please add relevant skills to improve your resume."

    skill_set = set(s.lower() for s in skills)

    if 'python' in skill_set and 'machine learning' in skill_set:
        recommendations.append("ML Engineer")
    if 'web development' in skill_set or 'django' in skill_set or 'html' in skill_set:
        recommendations.append("Web Developer")
    if 'data analysis' in skill_set or 'pandas' in skill_set:
        recommendations.append("Data Analyst")
    if 'java' in skill_set and 'spring' in skill_set:
        recommendations.append("Backend Developer")
    if not recommendations:
        recommendations.append("Software Engineer")

    
    ai_guidance = get_ai_career_guidance(skills, score)

    return recommendations, ai_guidance


# Home view
def home(request):
    return render(request, 'core/home.html')

# Signup view
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('upload_resume')
        else:
            messages.error(request, 'There was an error creating your account. Please fix the errors below.')
    else:
        form = UserCreationForm()
        
    return render(request, 'core/signup.html', {'form': form})

# Upload resume + results view
@login_required
def upload_resume(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST' and 'resume' in request.FILES:
        profile.resume = request.FILES['resume']
        profile.save()

        resume_path = profile.resume.path

        
        parsed_data = parse_resume(resume_path)

        
        resume_text = extract_text_from_pdf(resume_path)
        extracted = extract_data_from_text(resume_text)

        
        full_data = {
            'email': extracted.get('email'),
            'phone': extracted.get('phone'),
            'linkedin': extracted.get('linkedin'),
            'github': extracted.get('github'),
            'skills': parsed_data.get('skills', []),
            'education': parsed_data.get('education', []),
            'experience': parsed_data.get('experience', [])
        }

        score = calculate_resume_score(full_data)
        job_roles, guidance = get_recommendations(full_data['skills'], score)
        realtime_jobs = fetch_jobs(full_data['skills'])

        # Save to DB
        profile.skills = ', '.join(full_data['skills'])
        profile.education = ', '.join(full_data['education'])
        profile.experience = ', '.join(full_data['experience'])
        profile.feedback = "Resume parsed successfully!"
        profile.save()

        context = {
            'uploaded': True,
            'data': {
                'email': full_data['email'],
                'phone': full_data['phone'],
                'linkedin': full_data['linkedin'],
                'skills': full_data['skills'],
                'education': full_data['education'],
                'experience': full_data['experience'],
                'score': score,
                'job_roles': job_roles,
                'guidance': guidance,
                'realtime_jobs': realtime_jobs
            }
        }

        return render(request, 'core/upload_resume.html', context)

    return render(request, 'core/upload_resume.html', {'data': None})


@csrf_exempt
def chat_bot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('question', '').strip()
            if not user_input:
                return JsonResponse({'answer': "Please enter a question."})

            import requests

            # TOGETHER API
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "mistralai/Mistral-7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": "You are an AI career assistant that helps with resume advice, job suggestions, and interview tips."},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                output = response.json()
                reply = output['choices'][0]['message']['content']
                return JsonResponse({'answer': reply.strip()})
            else:
                return JsonResponse({'answer': f"API Error: {response.text}"}, status=500)

        except Exception as e:
            return JsonResponse({'answer': f"Error: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ai_career_guidance(skills, score):
    prompt = f"""
A user has the following skills: {', '.join(skills)}.
Their resume score is {score}/100.

Provide a personalized career guidance message for the user (not just job roles). The message should include:
- Analysis of their strengths
- Career path suggestions
- Recommended next steps (e.g., courses, projects, certifications)
- Encouragement based on current tech trends

Write it as a short personalized message, not a list.
"""


    headers = {
        "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # You can change to LLaMA-3 if needed
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