from __future__ import absolute_import, unicode_literals

import re
import soundcloud
import os
import vlc
from websocket import create_connection
import sys


class NuimoEvent(object):
    """
    A wrapper around the raw Nuimo websocket data. Maps the event to a verb and a value
    such as 'B' and 1 for button pressed.

    """

    def __init__(self, raw_event):
        """
        :param raw_event: the char string received from the Nuimo
        :return:
        """
        self.raw_event = raw_event
        self._verb, self._value = self.decode_raw_event(raw_event)
        super(NuimoEvent, self).__init__()


    def decode_raw_event(self, raw_event):
        """
        Returns a verb and value from a raw event, such as ('B','1') for button pressed.
        :return:
        """
        verb, value = re.match('([BRS])\,([LRUD]?[-?\d]*)', self.raw_event).groups()
        return verb, value


    @property
    def verb(self):
        return self._verb


    @property
    def value(self):
        return self._value


    def __unicode__(self):
        """
        Return the raw event data
        :return:
        """
        return self.raw_event


class SoundCloudPlaylistVLCController(object):
    """
    A high-level interface to the media player for one SoundCloud playlist using VLC
    """

    def __init__(self, playlist_permalink):
        self.permalink = playlist_permalink

        print 'Loading playlist {0}'.format(playlist_permalink)
        client_id = os.getenv("CLIENT_ID")
        self.soundcloud_client = soundcloud.Client(client_id=client_id)

        playlist_id = self.soundcloud_client.get('/resolve', url=playlist_permalink).__getattr__("id")
        playlist_resource = self.soundcloud_client.get('/playlists/' + str(playlist_id))
        track_list = []
        for track in playlist_resource.__getattr__("tracks"):
            track_list.append(track['id'])
        self.playlist = track_list

        self.player_instance = vlc.Instance()
        self.media_player = self.player_instance.media_player_new()

        self.current_track = 0
        self.play_track_from_list(0)

        super(SoundCloudPlaylistVLCController, self).__init__()

    def play_track_from_list(self, track_number):
        soundcloud_track_id = self.playlist[track_number]
        print 'Playing track number {0} with id {1}'.format(track_number, soundcloud_track_id)

        self.current_track = track_number
        track = self.soundcloud_client.get('/tracks/{0}'.format(soundcloud_track_id), allow_redirects=False)
        stream_url = self.soundcloud_client.get(track.stream_url, allow_redirects=False)
        stream_location = stream_url.location

        media = self.player_instance.media_new(stream_location)
        self.media_player.set_media(media)
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def resume(self):
        self.media_player.play()

    def skip_to_next_track(self):
        next_track = self.current_track + 1
        self.play_track_from_list(next_track)

    def skip_to_previous_track(self):
        next_track = self.current_track - 1
        self.play_track_from_list(next_track)

    def change_volume(self, percentage_delta):
        percentage = min(100, percentage_delta) if percentage_delta > 0 else max(-100, percentage_delta)
        print 'Changing volume by {0}%'.format(percentage)
        current_volume = self.media_player.audio_get_volume()
        self.media_player.audio_set_volume(current_volume + percentage)


class Dispatcher(object):
    def __init__(self, player):
        self.player = player
        self.player_is_playing = True

    def button_pressed(self):
        if self.player_is_playing:
            self.player.pause()
        else:
            self.player.stop()

    def rotation(self, delta):
        delta_value = int(delta)
        percentage_delta = float(min(30.0, delta_value)) / 30.0 * 100.0 if delta_value > 0 else float(max(-30, delta_value)) / 30.0 * 100.0
        self.player.change_volume(int(percentage_delta))
    def swipe(self, direction):
        if direction == 'R':
            self.player.skip_to_next_track()
        else:
            self.player.skip_to_previous_track()

def run_interface():
    """
    Main module entry point,
    run with the permalink of the playlist you want to control as command line argument
    requires the environment variables CLIENT_ID and VLC_PLUGIN_PATH

     e.g. VLC_PLUGIN_PATH=/Applications/VLC.app/Contents/MacOS/ CLIENT_ID=123abc python nuimo-using-vlc-wrapper.py https://soucloud.com/forss/sets/ecclesia
    :return:
    """
    ws = create_connection('ws://localhost:8086/')

    playlist_permalink = sys.argv[1]
    player = SoundCloudPlaylistVLCController(playlist_permalink)

    dispatcher = Dispatcher(player)


    try:
        while True:
            event = NuimoEvent(ws.recv())
            print(event.verb, event.value)

            if event.verb == 'B' and event.value == '0':
                dispatcher.button_pressed()
            elif event.verb == 'R':
                dispatcher.rotation(event.value)
            elif event.verb == 'S':
                dispatcher.swipe(event.value)

    except KeyboardInterrupt:
        pass

    finally:
        ws.close()


if __name__ == '__main__':
    run_interface()

