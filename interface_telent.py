"""
This file implements an interface to VLC over telnet, receiving events form the Nuimo over a websocket
and sending commands to VLC over Telnet.

"""
from __future__ import absolute_import, unicode_literals

import re
import telnetlib
#import Image, ImageFont, ImageDraw



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
        # http://www.regexr.com/3d4tq
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


class NuimoGlyphs(object):
    """
    A class consisting of Nuimo graphics objects.
    """
    def __init__(self):
        self.char_cache = {}
        super(NuimoGlyphs, self).__init__()

    def get_bitmap(self, char):
        if char in char_cache:
            return char_cache[char]



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

    def pause(self):
        """
        Pause media playback.
        :return:
        """

    def skip_forward(self):
        """
        Skip forward in media playback.
        :return:
        """
        pass

    def skip_backward(self):
        """
        Skip backward in media playback.
        :return:
        """
        pass

    def increase_volume(self, value):
        """
        Increase media player volume.
        :return:
        """
        pass

    def decrease_volume(self, value):
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
        self.connection = telnetlib.Telnet('localhost', 4212)
        self.connection.read_until('Password: ')
        self.connection.write(b'secret\n')
        print self.connection.read_until('>')
        super(TelnetVlcController, self).__init__()

    def play(self):
        print self.connection.write(b'play\n')

    def pause(self):
        print self.connection.write(b'pause\n')

    def stop(self):
        print self.connection.write(b'stop\n')

    def skip_forward(self):
        print self.connection.write(b'next\n')

    def skip_backward(self):
        print self.connection.write(b'prev\n')

    def increase_volume(self, value):
        s = b'volup {:d}\n'.format(value)
        print self.connection.write(s)

    def decrease_volume(self, value):
        s = b'voldown {:d}\n'.format(value)
        print self.connection.write(s)


class NuimoController(object):
    """
    A stateful media controller object.
    """
    def __init__(self, player_interface):
        self.player_interface = player_interface
        self.nuimo_states = {
            'button_pressed': False
        }
        self.player_states = {
            'playing': False
        }
        super(NuimoController, self).__init__()

    def _button_press(self):
        """
        Nuimo button has been pressed
        :return:
        """
        print('button press', 'player state: ', self.player_states['playing'])
        if self.player_states['playing'] is False:
            self.player_interface.play()
            self.player_states['playing'] = True
        else:
            self.player_interface.pause()
            self.player_states['playing'] = False

    def process_event(self, event):
        """
        Process an event from the Nuimo controller
        :param event:
        :return:
        """
        if event.verb == 'B':
            if event.value == '1':
                self.nuimo_states['button_pressed'] = True
            else:
                if self.nuimo_states['button_pressed'] is True:
                    self._button_press()
                self.nuimo_states['button_pressed'] = False

        elif event.verb == 'R':
            if event.value > 0:
                self.player_interface.increase_volume(min(1, int(int(event.value) / 16.0)))
            else:
                self.player_interface.decrease_volume(min(1, int(int(event.value) / -16.0)))

        elif event.verb == 'S':
            if event.value == 'R':
                self.player_interface.skip_forward()
                self.player_states['playing'] = True
            elif event.value == 'L':
                self.player_interface.skip_backward()
                self.player_states['playing'] = True
            elif event.value == 'D':
                self.player_interface.stop()
                self.player_states['playing'] = False


def run_interface():
    """
    Main module entry point
    :return:
    """
    from websocket import create_connection

    ws = create_connection('ws://localhost:8086/')
    nuimo = NuimoController(TelnetVlcController())

    try:
        while True:
            event = NuimoEvent(ws.recv())
            print "Received '%s'" % event
            print(event.verb, event.value)
            nuimo.process_event(event)

    except KeyboardInterrupt:
        pass

    finally:
        ws.close()


if __name__ == '__main__':
    run_interface()

