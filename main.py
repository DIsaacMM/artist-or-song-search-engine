from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json 

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    
    if result.status_code != 200:
        raise Exception(f"Failed to get token: {result.status_code}, {result.text}")
    
    json_result = result.json()
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"  # Solo aparecerá el primer artista
    query_url = url + query
    result = get(query_url, headers=headers)
    
    if result.status_code != 200:
        raise Exception(f"Failed to search artist: {result.status_code}, {result.text}")
    
    json_result = result.json().get('artists').get('items')

    if len(json_result) == 0:
        print(" --- Artists not found ---")
        return None
    return json_result[0]

def get_songs_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country-US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = result.json().get('tracks')
    return json_result
# Obtener el token y buscar un artista
token = get_token()
result = search_artist(token, "Pink Floyd")
print(result["name"])

artist_id = result["id"]

songs = get_songs_artist(token, artist_id)

for i, song in enumerate(songs):
    print(f"{i + 1}. {song['name']}")