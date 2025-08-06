
import requests

ADZUNA_APP_ID = '48cd929b'
ADZUNA_APP_KEY = 'fc10c0373526c703d5ba5781c170aba7'

def fetch_jobs(skills, location="India", max_results=5):
    if not skills:
        return []

    query = '+'.join(skills[:3])  

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'results_per_page': max_results,
        'what': query,
        'where': location
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            jobs = response.json().get('results', [])
            return [
                {
                    'title': job['title'],
                    'company': job.get('company', {}).get('display_name', ''),
                    'location': job.get('location', {}).get('display_name', ''),
                    'description': job['description'],
                    'apply_link': job['redirect_url']
                }
                for job in jobs
            ]
        else:
            return []
    except:
        return []
