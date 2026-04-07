
import sqlite3  
import json
import os
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd 
import numpy as np


DATABASE = "songs.db"
PROFILE_FILE = "user_profile.json"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn




def load_songs():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    songs = conn.execute("SELECT * FROM songs").fetchall()
    conn.close()
    return [dict(song) for song in songs]

def load_profile():
    # if profile doesn't exist
    if not os.path.exists(PROFILE_FILE):
        return {
            "name": "default",
            "danceability": 1.0,
            "energy": 1.0,
            "valence": 1.0,
            "tempo": 1.0,
            "loudness": 1.0,
            "speechiness": 1.0,
            "liked_songs": []
        }
    # if profile exists
    with open(PROFILE_FILE, "r") as f:
        profile = json.load(f)

    return profile

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)


def recommend_songs(profile, song_title, top_n):
    song_title = song_title.lower()
    songs = load_songs()
    df = pd.DataFrame([dict(song) for song in songs])
    FEATURES = [
        "danceability",
        "energy",
        "tempo",
        "valence",
        "loudness",
        "speechiness"
    ]
    for feature in FEATURES:
        df[feature] *= profile[feature]
    x=df[FEATURES].values
    scaler=StandardScaler()
    XScaled=scaler.fit_transform(x)
    matrix_file="similarity_matrix.npy"
    if os.path.exists(matrix_file):
        similarity_matrix=np.load(matrix_file)
    else:
        similarity_matrix=cosine_similarity(XScaled)
        np.save(matrix_file,similarity_matrix)
    if song_title not in df["name"].str.lower().values:
        return []

    idx = df[df["name"].str.lower() == song_title].index[0]

    similarity_scores = list(enumerate(similarity_matrix[idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    db=get_db_connection()
    list(db.execute("SELECT name FROM artists JOIN songs ON artists.id = songs.artist_id WHERE songs.name = ?", (song_title,))
    recommendations = []
    for i, score in similarity_scores[1:top_n+1]:
        recommendations.append({
            "title": df.iloc[i]["name"],
            "artist": df.iloc[i]["artist_id"],
            "similarity": round(score, 2)
        })
    return recommendations

def update_profile(profile, song, feedback):
    change = 0.1 if feedback == "like" else -0.1

    # update user preference weights
    profile["danceability"] += song["danceability"] * change
    profile["energy"] += song["energy"] * change
    profile["tempo"] += song["tempo"] * change / 200
    profile["valence"] += song["valence"] * change
    profile["loudness"] += song["loudness"] * change
    profile["speechiness"] += song["speechiness"] * change

    # track liked songs for the /liked page
    if feedback == "like":
        
        if song["name"] not in profile["liked_songs"]:
            profile["liked_songs"].append(song["name"])

    return profile