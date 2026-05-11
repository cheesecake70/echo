# imports

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from utils import (
    load_songs,
    load_profile,
    recommend_songs,
    save_profile,
    update_profile
)


# configure application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session to work


@app.route("/", methods=["GET", "POST"])
def index():
    songs = load_songs()
    profile = load_profile()

    song_titles = [song["name"] for song in songs]

    recommendations = []
    error = None
    selected_song = None
    show_more_button = False
    feedbacked_songs = session.get("feedbacked_songs", [])

    # Restore recommendations after feedback redirect
    if "last_song" in session:
        selected_song = session.pop("last_song")
        top_n = session.pop("last_top_n", 3)
        recommendations = recommend_songs(profile, selected_song, top_n)
        show_more_button = True

    # retrieve top_n from form, or default to 3
    top_n = int(request.form.get("top_n", 3))
    if request.method == "POST":
        if "song_title" in request.form:
            session.pop("feedbacked_songs", None)   # reset on new search
            selected_song = request.form["song_title"]

            if selected_song not in song_titles:
                error = "Song not found. Please select from the list."
            else:
                recommendations = recommend_songs(
                    profile,
                    selected_song,
                    top_n
                )
                show_more_button = True

        if "feedback" in request.form:
            feedback = request.form["feedback"]
            rec_song_title = request.form["rec_song_title"].strip()
            selected_song = request.form["base_song"].strip()

            try:
                song = next(song for song in songs if song["name"] == rec_song_title)
            except StopIteration:
                print(f"ERROR: Song '{rec_song_title}' not found in database")
                print(f"Available songs: {[s['name'] for s in songs]}")
                return redirect(url_for('index'))

            profile = update_profile(profile, song, feedback)
            save_profile(profile)

            # Store session state for page restoration
            session["last_song"] = selected_song
            session["last_top_n"] = top_n

            # track which songs got feedback
            feedbacked = session.get("feedbacked_songs", [])
            feedbacked.append(rec_song_title)
            session["feedbacked_songs"] = feedbacked

            # Verify the save
            saved_profile = load_profile()
            print(f"DEBUG: Feedback={feedback}, Song={rec_song_title}, Liked songs in saved profile: {saved_profile.get('liked_songs', [])}")

            # Redirect to refresh the page with updated data
            return redirect(url_for('index'))

        if "more" in request.form:
            selected_song = request.form["base_song"]
            top_n += 2
            recommendations = recommend_songs(
                profile,
                selected_song,
                top_n
            )
            show_more_button = False

    return render_template(
        "index.html",
        song_titles=song_titles,
        recommendations=recommendations,
        selected_song=selected_song,
        error=error,
        show_more_button=show_more_button,
        feedbacked_songs=feedbacked_songs
    )


@app.route("/liked")
def liked():
    profile = load_profile()
    liked_songs = profile.get("liked_songs", [])

    if liked_songs:
        songs = load_songs()
        liked_songs_details = [song for song in songs if song["name"] in liked_songs]
    else:
        liked_songs_details = []

    return render_template("liked.html", liked_songs=liked_songs_details)


# run
if __name__ == "__main__":
    app.run(debug=True)