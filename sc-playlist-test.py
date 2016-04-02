import soundcloud
import os

client_id = os.getenv("CLIENT_ID")
client = soundcloud.Client(client_id=client_id)

playlist_id = client.get('/resolve', url='https://soundcloud.com/forss/sets/ecclesia').__getattr__("id")
playlist_resource = client.get('/playlists/' + str(playlist_id))
track_list = []
for track in  playlist_resource.__getattr__("tracks"):
    stream_url = client.get(track['stream_url'], allow_redirects=False)
    stream_location = stream_url.location
    track_list.append(stream_location)
print track_list