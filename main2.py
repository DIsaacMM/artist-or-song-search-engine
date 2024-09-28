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


class Artist():
    def __init__(self, token, nombre): 
        self.__token = token
        self.__nombre = nombre
        self.__id = self.search_artist()["id"]
        self.__genero = self.search_artist()['genres']
        self.__seguidores = self.search_artist()['followers']['total']



    def search_artist(self):
        url = "https://api.spotify.com/v1/search"
        headers = get_auth_header(self.__token)
        query = f"?q={self.__nombre}&type=artist&limit=1"  # Solo aparecerá el primer artista
        query_url = url + query
        result = get(query_url, headers=headers)
        
        if result.status_code != 200:
            raise Exception(f"Failed to search artist: {result.status_code}, {result.text}")
        
        json_result = result.json().get('artists').get('items')

        if len(json_result) == 0:
            print(" --- Artists not found ---")
            return None
        return json_result[0]

    def get_songs_artist(self):
        url = f"https://api.spotify.com/v1/artists/{self.__id}/top-tracks?country-US"
        headers = get_auth_header(self.__token)
        result = get(url, headers=headers)

        if result.status_code != 200:
            raise Exception(f"Failed to get songs: {result.status_code}, {result.text}")
        
        json_result = result.json().get('tracks')
        return json_result

    def info(self): 
        print(f"Nombre Artista: {self.__nombre}")
        print(f"ID: {self.__id}")
        print(f"Generos: ")
        for i, genre in enumerate(self.__genero):
            print(f"\t{i + 1}. {genre}")
        print(f"Seguidores: {self.__seguidores}")
        print(f"Canciones: ")
        for i, song in enumerate(self.get_songs_artist()):
            print(f"\t{i + 1}. {song['name']}")



class Song(): 
    def __init__(self, token, titulo): 
        self.__token = token
        self.__titulo = titulo
        # Estas son las ubicaciones de la informacion dentro del api
        self.__album = self.search_song()['album']['name']
        self.__artist = self.search_song()['artists'][0]['name']
        self.__release_date = self.search_song()['album']['release_date']
        self.__track_number = self.search_song()['track_number']

    def search_song(self):
        url = "https://api.spotify.com/v1/search"
        headers = get_auth_header(self.__token)
        query = f"?q={self.__titulo}&type=track&limit=1"  # Solo aparecerá la primera canción
        query_url = url + query
        result = get(query_url, headers=headers) 

        if result.status_code != 200:
            raise Exception(f"Failed to search Song: {result.status_code}, {result.text}")
    
        json_result = result.json().get('tracks').get('items')

        if len(json_result) == 0:
            print(" --- Song not found ---")
            return None
        return json_result[0]

    # Imprime info de la cancion 
    def info(self):
        print(f"Nombre cancion: {self.__titulo}")
        print(f"Album: {self.__album}")
        print(f"Artista: {self.__artist}")
        print(f"Fecha de publicacion: {self.__release_date}")
        print(f"Numero de pista en album: {self.__track_number}")


# Obtener el token y buscar un artista
token = get_token()

# Artista
nombre = input("Introduce nombre de artista: ")
artista = Artist(token, nombre)
artista.info()


# Cancion
titulo = input("Introduce nombre de cancion: ")
cancion = Song(token, titulo)
cancion.info()