from abc import abstractmethod
from dotenv import load_dotenv
import os
import base64
import requests
from requests import post, get
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO

# Cargar las credenciales desde el archivo .env
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

class Buscador:
    def __init__(self, token):
        self.__token = token 

    def download_image(self, url):       
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            messagebox.showerror("Error", f"Failed to download image: {response.status_code}")
            return None

    def resize_image(self, img, url):
        img = self.download_image(url)
        max_width = 200
        max_height = 200

        og_width, og_height = img.size # Se obtiene el tamano de la imagen
        ratio = og_width / og_height  # Obtiene la relacion de tamano de la imagen

        if og_width > og_height: # Si es mas ancha que alta
            new_width = min(max_width, og_width) # ajusta el nuevo ancho
            new_height = int(new_width / ratio) # calcula una nueva altura
        else:
            new_height = min(max_height, og_height) # ajusta la altura
            new_width = int(new_height * ratio) # calcula un nuevo ancho

        return img.resize((new_width, new_height)) # El Image.Antialias ayuda a mejorar calidad 

    @abstractmethod
    def show_image(self, url):
        pass

    @abstractmethod
    def info(self): 
        pass

class Artist(Buscador):
    def __init__(self, token, nombre): 
        super().__init__(token)
        self.__nombre = nombre
        self.__id = self.search_artist()["id"]
        self.__genero = self.search_artist()['genres']
        self.__seguidores = self.search_artist()['followers']['total']
        self.__imagen = self.search_artist()['images'][0]['url']

    def search_artist(self):
        url = "https://api.spotify.com/v1/search"
        headers = get_auth_header(token)
        query = f"?q={self.__nombre}&type=artist&limit=1"
        query_url = url + query
        result = get(query_url, headers=headers)
        
        if result.status_code != 200:
            messagebox.showerror("Error", f"Failed to search artist: {result.status_code}, {result.text}")
            return None
        
        json_result = result.json().get('artists').get('items')

        if len(json_result) == 0:
            messagebox.showinfo("Info", "Artists not found")
            return None
        return json_result[0]

    def get_songs_artist(self):
        url = f"https://api.spotify.com/v1/artists/{self.__id}/top-tracks?country=US"
        headers = get_auth_header(token)
        result = get(url, headers=headers)

        if result.status_code != 200:
            messagebox.showerror("Error", f"Failed to get songs: {result.status_code}, {result.text}")
            return []
        
        json_result = result.json().get('tracks')
        return json_result
        
    def show_image(self, url):
        img = self.download_image(url)
        if img:
            img = self.resize_image(img, url) # cambia el tamano de la imagen
            img_tk = ImageTk.PhotoImage(img)
            lbl_image = tk.Label(ventana, image = img_tk)
            lbl_image.image = img_tk  # Ayuda a evitar el garbage collection
            lbl_image.grid(row=5, column=1, padx=10, pady=5)

    def info(self): 

        lbl_nombre = tk.Label(ventana, text = f"Nombre Artista: {self.__nombre}")
        lbl_nombre.grid(row=1, column=0, padx=10, pady=5)

        lbl_ID = tk.Label(ventana, text = f"ID: {self.__id}")
        lbl_ID.grid(row=2, column=0, padx=10, pady=5)

        lbl_seguidores = tk.Label(ventana, text=f"Seguidores: {self.__seguidores}")
        lbl_seguidores.grid(row=3, column=0, padx=10, pady=5)

        lbl_genero = tk.Label(ventana, text=f"Generos:")
        lbl_genero.grid(row=4, column=0, padx=10, pady=5)

        # Se crea el treeview
        tree = ttk.Treeview(ventana, columns = ("Genero"), show = "headings")
        tree.heading("Genero", text = "Genero")
        tree.grid(row=5, column=0, columnspan = 1, padx=10, pady=5, sticky = "nsew")

        # Se agregan generos al treeview
        for genre in self.__genero: 
            tree.insert("", "end", values=(genre))

        lbl_canciones = tk.Label(ventana, text=f"Canciones: ")
        lbl_canciones.grid(row=6, column=0, padx=10, pady=5)

        tree = ttk.Treeview(ventana, columns = ("Nombre", "Album", "Duracion", "Pista"), show = "headings")
        tree.heading("Nombre", text = "Nombre") 
        tree.heading("Album", text = "Album") 
        tree.heading("Duracion", text = "Duracion") 
        tree.heading("Pista", text = "Pista") 
        tree.grid (row=7, column=0, columnspan = 4, padx=10, pady=5, sticky = "nsew")

        # Se agregan las canciones al treeview

        canciones = self.get_songs_artist()
        for song in canciones:
            duration_ms = song["duration_ms"]
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            duration = f"{minutes}:{seconds:02d}"
            tree.insert("", "end", values=(song["name"], song["album"]["name"], duration, song['track_number'])) 

        self.show_image(self.__imagen)

        ventana.update() # Actualiza la ventana permitiendo mostrar lo que hay en el metodo

class Song(Buscador): 
    def __init__(self, token, titulo): 
        self.__token = token
        self.__titulo = titulo
        # Estas son las ubicaciones de la informacion dentro del api
        self.__album = self.search_song()['album']['name']
        self.__artist = self.search_song()['artists'][0]['name']
        self.__release_date = self.search_song()['album']['release_date']
        self.__track_number = self.search_song()['track_number']
        self.__imagen = self.search_song()['album']['images'][0]['url']

    def search_song(self):
        url = "https://api.spotify.com/v1/search"
        headers = get_auth_header(token)
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
    
    def show_image(self, url):
        img = self.download_image(url)
        if img:
            img = self.resize_image(img, url) # cambia el tamano de la imagen
            img_tk = ImageTk.PhotoImage(img)
            lbl_image = tk.Label(ventana, image = img_tk)
            lbl_image.image = img_tk  # Ayuda a evitar el garbage collection
            lbl_image.grid(row=5, column=4, padx=10, pady=5)
   
    # Imprime info de la cancion 
    def info(self):
        lbl_titulo = tk.Label(ventana, text=f"Nombre Cancion: {self.__titulo}")
        lbl_titulo.grid(row=1, column=3, padx=10, pady=5)

        lbl_Album = tk.Label(ventana, text=f"Album: {self.__album}")
        lbl_Album.grid(row=2, column=3, padx=10, pady=5)

        lbl_Autor = tk.Label(ventana, text=f"Artista: {self.__artist}")
        lbl_Autor.grid(row=3, column=3, padx=10, pady=5)

        lbl_lbl_publicacion = tk.Label(ventana, text = f"Fecha de publicacion: {self.__release_date}")
        lbl_lbl_publicacion.grid(row=4, column=3, padx=10, pady=5)

        lbl_pista = tk.Label(ventana, text=f"Pista: {self.__track_number}")
        lbl_pista.grid(row=5, column=3, padx=10, pady=5)

        self.show_image(self.__imagen)

        ventana.update() # Actualiza la ventana permitiendo mostrar lo que hay en el metodo

# Funciones event
def buscar_A(event=None): # El event = None permite que la funcion funcione al presionar el Enter
    token = get_token()
    artista = Artist(token, input_artista.get())
    artista.info()
    ventana.update()

def buscar_C(event=None): # El event = None permite que la funcion funcione al presionar el Enter
    artista = Song(token, input_cancion.get())
    artista.info()
    ventana.update()

# Obtener el token
token = get_token()

ventana = tk.Tk()
ventana.geometry('1300x700')
ventana.title("Libreria Artistas y Canciones")

# Artista 
lbl_artista = tk.Label(ventana, text = "Introduce nombre de artista: ")
lbl_artista.grid(row=0, column=0, padx=10, pady=5)

input_artista = tk.Entry(ventana)
input_artista.grid(row=0, column=1, padx=10, pady=5)
input_artista.bind("<Return>", buscar_A)  # El Return permite usar solo el Enter 

# Cancion 

lbl_cancion = tk.Label(ventana, text = "Introduce nombre de cancion: ")
lbl_cancion.grid(row=0, column=2, padx=10, pady=5)

input_cancion = tk.Entry(ventana)
input_cancion.grid(row=0, column=3, padx=10, pady=5)
input_cancion.bind("<Return>", buscar_C)  # El Return permite usar solo el Enter 

ventana.mainloop()