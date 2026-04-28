# lms-service/main.py
from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI(title='LMS Service', version='1.0')

# Reads from environment variable — different for Docker Compose vs Kubernetes
RECOMMENDER_URL = os.getenv('RECOMMENDER_URL', 'http://recommender:8001')


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'lms'}


@app.get('/lms/courses')
async def get_courses():
    courses = [
        {'id': i, 'title': f'Course {i}', 'topic': f'Topic {(i % 5) + 1}'}
        for i in range(1, 31)
    ]
    return {'courses': courses, 'total': len(courses)}


@app.get('/lms/recommendations/{user_id}')
async def get_recommendations(user_id: int):
    """Main endpoint — calls recommender service and returns results."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f'{RECOMMENDER_URL}/recommend/{user_id}'
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail='Recommender service unavailable'
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail='Recommender service timeout'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))