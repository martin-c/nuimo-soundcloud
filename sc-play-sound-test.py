import soundcloud
import time
import vlc
import os

client_id = os.getenv("CLIENT_ID")
client = soundcloud.Client(client_id=client_id)

track_id = client.get('/resolve', url='http://soundcloud.com/forss/voca-nomen-tuum').__getattr__("id")
track = client.get('/tracks/' + str(track_id))
stream_url = client.get(track.stream_url, allow_redirects=False)
stream_location = stream_url.location

player_instance = vlc.Instance()
player = player_instance.media_player_new()
media = player_instance.media_new(stream_location)
player.set_media(media)

player.audio_set_volume(50)
player.play()
time.sleep(5)

print player.audio_get_volume()

