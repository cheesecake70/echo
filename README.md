Echo — Song Recommender

CS50x Final Project

Video Demo: https://youtu.be/yLQUG0RXiD0

Description:

Echo is a web application that recommends songs based on musical similarity and learns each user's personal taste over time. We built it as our CS50x final project because we wanted to combine two things the course had gotten us excited about: building a real, usable full-stack web app with Flask, and applying a bit of the data-science toolkit (pandas, scikit-learn) to a problem that felt fun rather than academic. Instead of building yet another to-do list or e-commerce clone, we wanted a project where the "smart" part actually did something interesting under the hood, so we settled on a recommendation engine for music.

The idea behind Echo is simple to describe but was genuinely challenging to implement well: a user picks a song they like, and Echo suggests other songs from its catalog that sound similar, based on a handful of quantifiable audio characteristics such as danceability, energy, tempo, valence (musical positivity), loudness, and speechiness. What makes Echo different from a plain "find nearest neighbor" recommender is that every user has their own evolving taste profile, stored as a set of numeric weights over those same audio features. When a user likes or dislikes a recommended song, Echo nudges their weights up or down based on that song's characteristics, so someone who consistently likes high-energy, danceable tracks will gradually see their profile favor those features more strongly, and their future recommendations will shift accordingly. Two users who start from the same song will, after enough feedback, end up with noticeably different recommendation lists — which was exactly the behavior we were hoping to build.

Under the hood, the recommendation step works by taking the full catalog of songs, scaling each song's feature vector by the user's profile weights, standardizing the result with scikit-learn's StandardScaler so that no single feature (like loudness, which has a wider numeric range than danceability) dominates the distance calculation, and then computing cosine similarity between the chosen song and every other song in the weighted, standardized space. The songs with the highest similarity scores are returned as recommendations. Liked songs are saved permanently to the user's library, which they can revisit at any time on a separate page.

What each file does

app.py is the entry point of the application and defines every Flask route: registration and login for authentication, the home route where a logged-in user searches for a song and views/rates their recommendations, and a route for browsing previously liked songs. It also defines a login_required decorator, applied to any route that should only be reachable by an authenticated user, which checks the Flask session and redirects to the login page if it's missing or invalid. We kept almost all of the HTTP-facing logic — form validation, session handling, redirects, flashing error messages — in this file, so that it reads like a map of "what can a user actually do on this site," while pushing the more computational logic elsewhere.

utils.py is where the actual substance of the project lives, and it was by far the file we iterated on the most. It manages the SQLite connection and queries (including a join between the songs and artists tables so the app can display artist names without duplicating them across every song row), loads and persists each user's taste profile, and contains the recommendation function itself: scaling, standardizing, and running cosine similarity as described above. It also contains the function that updates a user's profile weights after a like or dislike, and the password hashing and verification logic (using Werkzeug's generate_password_hash/check_password_hash) that keeps app.py's auth routes free of raw password handling.

addurl.py is a small, standalone helper script we used while building and maintaining the song database — specifically for attaching supplementary data, such as external links, to existing song rows without having to hand-edit the database. It isn't part of the live request/response cycle of the app; it's a one-off data-preparation tool.

Beyond the Python files, songs.db is the SQLite database holding the songs, artists, users, user_profiles, and liked_songs tables, similarity_matrix.npy stores a precomputed similarity matrix we experimented with to speed up recommendations, and the templates/ and static/ directories hold the Jinja2 HTML templates and CSS respectively.

Design choices we debated

The biggest decision was whether to build a per-user weighted profile at all, versus a much simpler "songs similar to this song" recommender shared by every user. The simpler version would have been considerably less work, but it also would have made the "feedback" feature pointless — liking or disliking a song wouldn't actually change anything for that user. We decided the extra complexity was worth it, since watching recommendations visibly shift after a handful of likes and dislikes is, to us, the whole point of the project.

We also went back and forth on whether to precompute a full similarity matrix ahead of time (stored in similarity_matrix.npy) versus recomputing similarity on the fly for each request. A precomputed matrix is faster, but it's only valid for one fixed weighting of features — as soon as per-user weights entered the picture, a single global matrix could no longer capture everyone's personalized similarity space. We ultimately compute similarity on demand, weighted by the requesting user's profile, and accepted the small performance cost given the catalog size stayed manageable.

Finally, we chose Flask's built-in session-based authentication over anything more elaborate like JWTs, since the project runs as a single server without a separate API client, and CS50's scope didn't call for the added complexity of token refresh logic.

Features


User accounts — registration and login with hashed passwords (Werkzeug's pbkdf2:sha256)
Song search & recommend — pick a song and get a ranked list of similar tracks
Feedback loop — like/dislike recommendations to continuously personalize your taste profile
Liked songs library — view all songs you've liked in one place
"Show more" — expand the recommendation list without starting over


Tech stack


Backend: Flask (Python)
Data / ML: pandas, scikit-learn (StandardScaler, cosine_similarity)
Database: SQLite (songs.db)
Auth: Werkzeug password hashing + Flask sessions
Frontend: Jinja2 templates, HTML/CSS


Project structure

echo/
├── app.py                  # Flask routes: auth, recommend, feedback, liked songs
├── utils.py                # DB access, recommendation engine, profile updates
├── addurl.py                # Script for adding/updating song data (e.g. links)
├── requirements.txt
├── songs.db                 # SQLite database (songs, artists, users, profiles, liked songs)
├── similarity_matrix.npy    # Precomputed similarity data
├── templates/                # Jinja2 HTML templates (login, register, index, liked, etc.)
└── static/                   # CSS/JS/assets