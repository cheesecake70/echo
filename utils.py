
import sqlite3  
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd 
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "songs.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def load_songs():
    conn = get_db_connection()
    songs = conn.execute("SELECT *, artists.name AS artist_name FROM songs JOIN artists ON songs.artist_id = artists.id").fetchall()
    conn.close()
    return [dict(song) for song in songs]

def load_profile(user_id):
    db = get_db_connection()
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    if profile is None:
        db.execute("INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (user_id,))
        db.commit()
        profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return dict(profile) if profile else None

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
            "similarity": round(score, 2),
            "link": df.iloc[i]["yt_link"]
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
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def register_user(username, password):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, generate_password_hash(password, method='pbkdf2:sha256')))
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Username already taken."}
    finally:
        conn.close()

def verify_password(username, password):
    conn = get_db_connection()
    user = dict(conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone())
    conn.close()
    if user and check_password_hash((user["password"]), password):
        return dict(user)
    return None