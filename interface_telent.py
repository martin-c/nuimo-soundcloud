"""
This file implements an interface to VLC over telnet, receiving events form the Nuimo over a websocket
and sending commands to VLC over Telnet.

"""
from __future__ import absolute_import, unicode_literals

import re
import telnetlib


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
        import re
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


class MediaPlayerController(object):
    """
    A high-level interface to the media player
    """
    def play(self):
        """
        Begin media file playback.
        :return:
        """
        pass

    def stop(self):
        """
        Stop media file playback.
        :return:
        """
        pass

    def increase_volume(self):
        """
        Increase media player volume.
        :return:
        """
        pass

    def decrease_volume(self):
        """
        Decrease media player volume.
        :return:
        """
        pass


class TelnetVlcController(MediaPlayerController):
    """
    A controller for VLC media player over Telent interface
    """
    def __init__(self):
        self.connection = telnetlib.Telnet(localhost, 4212)
        super(TelnetVlcController, self).__init__()






def run_interface():
    """
    Main module entry point
    :return:
    """
    from websocket import create_connection

    ws = create_connection('ws://localhost:8086/')

    try:
        while True:
            event = NuimoEvent(ws.recv())
            print "Received '%s'" % event
            print(event.verb, event.value)
    except KeyboardInterrupt:
        pass

    finally:
        ws.close()


if __name__ == '__main__':
    run_interface()

