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


@app.route("/", methods=["GET", "POST"])
def index():
    songs = load_songs()
    profile = load_profile()

    song_titles = [song["name"] for song in songs]

    recommendations = []
    error = None
    selected_song = None
    show_more_button = False
    # retrieve top_n from form, or default to 3
    top_n = int(request.form.get("top_n", 3))
    if request.method == "POST":
        if "song_title" in request.form:
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
            rec_song_title = request.form["rec_song_title"]
            selected_song = request.form["base_song"]

            song = next(song for song in songs if song["name"] == rec_song_title)

            profile = update_profile(profile, song, feedback)
            save_profile(profile)
            
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
        show_more_button=show_more_button
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