# recommender-service/main.py
from fastapi import FastAPI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title='Recommender Service', version='1.0')

# ── Synthetic interaction matrix (generated once at startup) ──────────
NUM_USERS   = 200
NUM_COURSES = 30
SEED        = 42

rng = np.random.default_rng(SEED)
# ~20% density: most users have taken ~6 out of 30 courses
interaction_matrix = (rng.random((NUM_USERS, NUM_COURSES)) > 0.80).astype(float)

# Precompute user-user similarity matrix (200×200) at startup
user_similarity = cosine_similarity(interaction_matrix)
# ─────────────────────────────────────────────────────────────────────


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'recommender'}


@app.get('/recommend/{user_id}')
async def recommend(user_id: int, top_n: int = 5):
    """
    User-based collaborative filtering recommendation.
    Per-request cost: weighted cosine similarity sum O(U×C) — generates real CPU load.
    """
    uid = user_id % NUM_USERS

    # Weighted sum of similar users' course interactions
    sim_scores = user_similarity[uid]                     # shape (200,)
    weighted   = sim_scores @ interaction_matrix          # shape (30,)

    # Exclude courses the user has already taken
    weighted[interaction_matrix[uid] > 0] = 0

    # Return top-N course indices
    top_indices = np.argsort(weighted)[::-1][:top_n]

    return {
        'user_id':              user_id,
        'recommended_courses':  top_indices.tolist(),
        'total_recommendations': int(top_n),
    }