from time import sleep
from dotenv import dotenv_values
from ytmusicapi import YTMusic
import spotipy.util as util
import spotipy
import os
import sys
import webbrowser


class SpotTube():
    def __init__(self, clientId=None, clientSecret=None, redirectURI=None):
        
        self._clientId = clientId
        self._clientSecret = clientSecret
        self._redirectURI = redirectURI
        self._sp = None
        self.username = None
        
        scope = "playlist-modify-public playlist-modify-public playlist-read-private playlist-read-collaborative"
        
        try:
            access_token = util.prompt_for_user_token(
            client_id=self._clientId, 
            client_secret=self._clientSecret, 
            scope=scope, 
            redirect_uri=self._redirectURI,
            cache_path=".cache"
        )
        except Exception:
            print("Não foi possível autenticar em Spotify, verifique se suas credenciais estão corretas.\n")
            sys.exit()
        else:
            self._sp = spotipy.Spotify(access_token)
            self.username = self._sp.me()["display_name"]
            print(f"Conectado em Spotify como {self.username}")
       
        print("\nAutenticando em Youtube Music...\n")
        sleep(3)
       
        try:
            self._yt = YTMusic("headers_auth.json")
        except Exception:
            print("Não foi possível autenticar em Youtube Music, verifique se o arquivo headers.json está configurado corretamente\n")
            sys.exit()
        else:
            print("Conectado em Youtube Music\n")

  
    def main(self):
        userPlaylists = self.get_all_user_spotify_playlists()
        selected = self.select_playlist(userPlaylists)  
        musics = self.get_musics_from_spotify_playlist(selected[0])   
        videoIds = self.search_on_youtube(musics)
        self.add_musics_on_youtube(videoIds, selected[1])
        self.saveCredentials(client_id=self._clientId, client_secret=self._clientSecret, redirect_uri=self._redirectURI)


    def get_all_user_spotify_playlists(self):
        userPlaylists = {}
        playlists = self._sp.user_playlists(self._sp.me()["id"])["items"]
        print()
        for i in range(len(playlists)):
            if playlists[i]["owner"]["display_name"] == self.username:
                userPlaylists[playlists[i]["id"]] = playlists[i]["name"]

        return userPlaylists


    def select_playlist(self, playlists):
        choice = None
        options = []
        name = []
        print("Essas são as suas playlists que encontrei: \n")
        while True:
            for i, j in enumerate(playlists.items()):
                    print(f"{i+1}ª playlist: {j[1]}")
                    options.append(i+1)
                    name.append({"name": j[1], "id": j[0]})
            try:
                choice = int(input("\nSelecione uma playlist: "))
                if choice not in options:
                    os.system("cls")
                    print("Selecione uma playlist válida.\n")
                    continue
            except ValueError:
                os.system("cls")
                print("Selecione uma playlist válida.\n")
            else:
                os.system("cls")
                playlistName = name[choice - 1]["name"]
                print("Voce selecionou " + playlistName)
                choice = name[choice - 1]["id"]
                del name
                del options
                break
        return (choice, playlistName)


    def get_musics_from_spotify_playlist(self, playlistId):
        tracks = []
        songs = self._sp.playlist_tracks(playlistId)["items"]
        for i in range(len(songs)):
            tracks.append(songs[i]["track"]["name"])
        if len(songs) >= 100:
            songs = self._sp.playlist_tracks(playlistId, offset=100+1)["items"]
            for i in range(len(songs)):
                tracks.append(songs[i]["track"]["name"])
            return tracks
        return tracks


    def search_on_youtube(self, tracks):
        print("Buscando as músicas...\n")
        videoIds = {}
        for music in tracks:
            youtube = self._yt.search(query=music, filter="songs", ignore_spelling=True, limit=5)[0]
            videoIds[youtube["title"]] = youtube["videoId"]

        return videoIds


    def add_musics_on_youtube(self, ids, playlistName):

        names = [i for i in ids.keys()]
        all_ids = [i for i in ids.values()]

        [print(track) for track in names]
        print("\n")
        print("Adicionando músicas em sua playlist do Yt Music.\nAguarde alguns instantes...")
        
        sleep(5)

        playlist = self._yt.create_playlist(title=playlistName, description="", privacy_status="PRIVATE")
        self._yt.add_playlist_items(playlistId=playlist, videoIds=all_ids)
        print("\nAs músicas foram adicionadas!")
        browser = input("Pressione 1 para abrir no navegador ou pressione qualquer tecla para terminar: ")
        if browser == '1':
            webbrowser.open(f"https://music.youtube.com/playlist?list={playlist}")
        

    def saveCredentials(self, client_id, client_secret, redirect_uri):
        with open(".env", "w") as file:
            file.write(f"clientID={client_id}\n")
            file.write(f"clientSecret={client_secret}\n")
            file.write(f"URI={redirect_uri}\n")


def start(isDotEnv=False):
    if isDotEnv:

        keys = dotenv_values(dotenv_path=".env")

        clientID = keys["clientID"]
        clientSecretID = keys["clientSecret"] 
        redirectURI = keys["URI"]

        run = SpotTube(clientId=clientID, clientSecret=clientSecretID, redirectURI=redirectURI)
        run.main()
    else:
        client_id = input("clientID: ")
        client_secret = input("clientSecret: ")
        uri = input("Redirect_URI: ")

        run = SpotTube(clientId=client_id, clientSecret=client_secret, redirectURI=uri)
        run.main()


if __name__ == "__main__":
    try:
        if ".env" in os.listdir(os.getcwd()):
            start(isDotEnv=True)
        else:
            start()
    except (KeyboardInterrupt, EOFError):
        sys.exit()
    finally:
        try:
            os.remove(".cache")
        except FileNotFoundError:
            sys.exit()