from django.shortcuts import render, redirect
from django.conf import settings
import requests
from requests import post
import json
import os
from django.http import HttpResponse


def index(request):
    return render(request, 'music/index.html')

def authorize(request):
    scope = 'user-library-read playlist-modify-public playlist-modify-private'
    redirect_uri = settings.SPOTIFY_REDIRECT_URI
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={settings.SPOTIFY_CLIENT_ID}&scope={scope}&redirect_uri={redirect_uri}"
    return redirect(auth_url)

def callback(request):
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    redirect_uri = 'http://localhost:8000/callback'
    response = requests.post(token_url, {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'client_secret': settings.SPOTIFY_CLIENT_SECRET,
    })
    response_data = response.json()
    access_token = response_data.get('access_token')
    request.session['access_token'] = access_token
    return redirect('index')

def create_playlist(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('authorize')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    user_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    user_data = user_response.json()

    if 'id' not in user_data:
        return HttpResponse("Failed to retrieve user ID", status=400)

    user_id = user_data['id']

    playlist_response = requests.post(
        f'https://api.spotify.com/v1/users/{user_id}/playlists',
        headers=headers,
        json={
            'name': 'My Liked Songs Backup',
            'description': 'Playlist of liked songs from my old account',
            'public': True  # Ensure the playlist is public
        }
    )
    playlist_data = playlist_response.json()

    if 'id' not in playlist_data:
        return HttpResponse("Failed to create playlist", status=400)

    playlist_id = playlist_data['id']

    # Save the playlist ID in the session for future use
    request.session['last_playlist_id'] = playlist_id

    # Load the saved liked songs
    file_path = os.path.join(os.path.dirname(__file__), 'liked_songs.json')
    with open(file_path, 'r') as file:
        songs = json.load(file)

    track_uris = [song['track']['uri'] for song in songs]

    # Add songs to the new playlist
    for i in range(0, len(track_uris), 100):
        uris_chunk = track_uris[i:i+100]
        requests.post(
            f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
            headers=headers,
            json={'uris': uris_chunk}
        )

    return render(request, 'music/playlist_created.html', {'playlist_id': playlist_id})


def list_playlists(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('authorize')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    playlists_response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    playlists_data = playlists_response.json()

    return render(request, 'music/list_playlists.html', {'playlists': playlists_data['items']})


def like_songs_from_playlist(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('authorize')

    playlist_id = request.GET.get('playlist_id')
    if not playlist_id:
        return HttpResponse("No playlist ID found", status=400)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Fetch songs from the playlist
    track_ids = []
    offset = 0
    while True:
        response = requests.get(
            f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset={offset}&limit=100',
            headers=headers
        )
        data = response.json()
        items = data.get('items', [])
        track_ids.extend([item['track']['id'] for item in items])
        if len(items) < 100:
            break
        offset += 100

    # Like songs in batches of 50
    for i in range(0, len(track_ids), 50):
        ids_chunk = track_ids[i:i+50]
        response = requests.put(
            'https://api.spotify.com/v1/me/tracks',
            headers=headers,
            json={'ids': ids_chunk}
        )
        print(f"Chunk {i // 50 + 1} Response: {response.status_code} - {response.text}")

    return render(request, 'music/liked_songs_another.html', {'track_ids': track_ids})

def save_liked_songs(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('authorize')

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    songs = []
    limit = 50
    offset = 0

    while True:
        response = requests.get(
            f'https://api.spotify.com/v1/me/tracks?limit={limit}&offset={offset}',
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error fetching liked songs: {response.status_code} - {response.text}")
            break
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {response.text}")
            break
        
        items = data.get('items', [])
        songs.extend(items)
        
        if len(items) < limit:
            break
        
        offset += limit
    
    if songs:
        # Save songs to a JSON file
        file_path = os.path.join(os.path.dirname(__file__), 'liked_songs.json')
        with open(file_path, 'w') as file:
            json.dump(songs, file, indent=4)
    
    return render(request, 'music/saved_songs.html', {'songs': songs})

def list_account_playlists(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('authorize')

    username = request.GET.get('username')
    if not username:
        return HttpResponse("No username provided", status=400)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    playlists_response = requests.get(f'https://api.spotify.com/v1/users/{username}/playlists', headers=headers)
    
    if playlists_response.status_code != 200:
        return HttpResponse("Failed to fetch playlists", status=playlists_response.status_code)

    playlists_data = playlists_response.json()

    return render(request, 'music/list_account_playlists.html', {
        'playlists': playlists_data['items'],
        'username': username
    })


def search_account(request):
    return render(request, 'music/search_account.html')
