
import sqlite3  
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd 
import numpy as np


DATABASE = "songs.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def load_songs():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    songs = conn.execute("SELECT *, artists.name AS artist_name FROM songs JOIN artists ON songs.artist_id = artists.id").fetchall()
    conn.close()
    return [dict(song) for song in songs]

def load_profile(user_id):
    db = get_db_connection()
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return dict(profile)

def save_profile(user_id, profile):
    db = get_db_connection()
    db.execute("""
        UPDATE user_profiles SET
            danceability = ?,
            energy       = ?,
            tempo        = ?,
            valence      = ?,
            loudness     = ?,
            speechiness  = ?
        WHERE user_id = ?
    """, (
        profile["danceability"],
        profile["energy"],
        profile["tempo"],
        profile["valence"],
        profile["loudness"],
        profile["speechiness"],
        user_id
    ))
    db.commit()
    db.close()
    


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
    similarity_matrix=cosine_similarity(XScaled)
    if song_title not in df["name"].str.lower().values:
        return []

    idx = df[df["name"].str.lower() == song_title].index[0]

    similarity_scores = list(enumerate(similarity_matrix[idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    recommendations = []
    for i, score in similarity_scores[1:top_n+1]:
        recommendations.append({
            "title": df.iloc[i]["name"],
            "artist": df.iloc[i]["artist_name"],
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

    if feedback == "like":
        db = get_db_connection()
        db.execute(
            "INSERT OR IGNORE INTO liked_songs (user_id, song_id) VALUES (?, ?)",
            (profile["user_id"], song["id"])
        )
        db.commit()
        db.close()

    return profile

def get_liked_songs(user_id):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT songs.*, artists.name AS artist_name
        FROM liked_songs
        JOIN songs   ON liked_songs.song_id  = songs.id
        JOIN artists ON songs.artist_id      = artists.id
        WHERE liked_songs.user_id = ?
        ORDER BY liked_songs.liked_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

