from flask import Flask, render_template, request, redirect, url_for, json, session
import spotipy
from spotipy import oauth2
import os

import algs

app = Flask(__name__)

app.secret_key = algs.generateRandomString(16)

# GLOBAL VARIABLES

PORT_NUMBER = int(os.environ.get('PORT', 33507))
SPOTIPY_CLIENT_ID = '883896384d0c4d158bab154c01de29db'
SPOTIPY_CLIENT_SECRET = '37443ee0c0404c44b755f3ed97c48493'
SPOTIPY_REDIRECT_URI1 = 'http://localhost:8888/callback1'
SPOTIPY_REDIRECT_URI2 = 'http://localhost:8888/callback2'
SCOPE = 'user-library-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private'
CACHE = '.spotipyoauthcache'
STATE1 = algs.generateRandomString(16)
STATE2 = algs.generateRandomString(16)

sp_oauth1 = oauth2.SpotifyOAuth( SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,SPOTIPY_REDIRECT_URI1,state=STATE1,scope=SCOPE,cache_path=CACHE,show_dialog=True)
sp_oauth2 = oauth2.SpotifyOAuth( SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,SPOTIPY_REDIRECT_URI2,state=STATE2,scope=SCOPE,cache_path=CACHE,show_dialog=True)

TRACK_SAVE = None
TOKEN1 = None
TOKEN2 = None
INTERSECTION = None

SP1 = None
SP2 = None


# VIEWS

@app.route('/')
@app.route('/index')
def index():       
    auth_url1 = sp_oauth1.get_authorize_url()
    return render_template("first.html", auth_url=auth_url1)



@app.route('/callback1')
def callback1():
    global TOKEN1
    code = request.args.get('code')
    state = request.args.get('state')

    if code and state == STATE1:
        token = sp_oauth1.get_access_token(code)
        TOKEN1 = token
        return render_template("loading1.html")

    else:
        return redirect(url_for('index'))

@app.route('/getsongs1')
def getsongs1():
    global TRACK_SAVE
    global SP1
    token = TOKEN1
    access_token = token["access_token"]

    sp1 = spotipy.Spotify(auth=access_token)
    SP1 = sp1

    tracks1 = getAllTracks(sp1)
    #session["tracks1"] = tracks1
    TRACK_SAVE = tracks1

    auth_url2 = sp_oauth2.get_authorize_url()
    return render_template("second.html", auth_url=auth_url2)


@app.route('/callback2')
def callback2():
    global TOKEN2

    code = request.args.get('code')
    state = request.args.get('state')

    if code and state == STATE2:
        token = sp_oauth2.get_access_token(code)
        TOKEN2 = token
        return render_template("loading2.html")

    else:
        return "redirect(url_for('index'))"

@app.route('/getsongs2')
def getsongs2():
    global TRACK_SAVE
    global SP2
    global INTERSECTION
    token = TOKEN2
    access_token = token["access_token"]

    sp2 = spotipy.Spotify(auth=access_token)
    SP2 = sp2

    tracks2 = getAllTracks(sp2)
    tracks1 = TRACK_SAVE


    score = algs.CompatabilityIndex(tracks1, tracks2)

    top5artists = algs.TopNArtists(tracks1, tracks2, 5)

    intersection_songs = algs.IntersectionPlaylist(tracks1, tracks2)
    intersection_size = len(intersection_songs)
    INTERSECTION = intersection_songs

    return render_template("last.html", score=int(score), count=intersection_size, artists=top5artists, success_page=url_for('success'))

@app.route('/success')
def success():
    sp2 = SP2
    user_id = sp2.me()["id"]
    intersection_songs = INTERSECTION
    new_playlist = sp2.user_playlist_create(user_id, 'Compatify', public=False)

    size = len(intersection_songs)

    index = 0
    while True:
        current_num = size - index
        if current_num > 100:
            sp2.user_playlist_add_tracks(user_id, new_playlist["id"], intersection_songs[index:index+100], position=None)
            index += 100
        elif current_num > 0:
            sp2.user_playlist_add_tracks(user_id, new_playlist["id"], intersection_songs[index:index+current_num], position=None)
            break
        else:
            break
    return render_template("success.html")


# Methods

def getAllTracks(sp):
    tracks = []

    SONGS_PER_TIME = 50
    offset=0

    while True:
        SPTracks = sp.current_user_saved_tracks(limit=SONGS_PER_TIME, offset=offset) 

        if len(SPTracks["items"]) == 0:
        #if offset >= 50:
            break

        for song in SPTracks["items"]:
            track = song["track"]
            song_item = { "name": track["name"], "uri": track["uri"], "artist": track["artists"][0]["name"], "album": track["album"]["name"] }
            tracks.append(song_item)

        offset += SONGS_PER_TIME

    return tracks
'''
def createIntersection(sp):
    sp.user



'''


















if __name__ == '__main__':
    app.run(port=PORT_NUMBER, debug=True)