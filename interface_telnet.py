"""
This file implements an interface to VLC over telnet, receiving events form the Nuimo over a websocket
and sending commands to VLC over Telnet.

"""
from __future__ import absolute_import, unicode_literals

import re
import telnetlib
import math
#from PIL import Image, ImageFont, ImageDraw


class RawNuimoEvent(object):
    """
    A wrapper around the raw Nuimo websocket data. Maps the event to a verb and a value
    such as 'B' and 1 for button pressed.

    """
    def __init__(self, raw_event):
        """
        :param raw_event: the char string received from the Nuimo
        :return:
        """
        self._action, self._value = self.decode_raw_event(raw_event)
        super(RawNuimoEvent, self).__init__()

    def decode_raw_event(self, raw_event):
        """
        Returns an action and value from a raw event, such as ('B','1') for button pressed.
        :return:
        """
        # http://www.regexr.com/3d4tq
        action, value = re.match(r'([BRS]),([LRUD]?[-?\d]*)', raw_event).groups()
        return action, value

    @property
    def action(self):
        """
        Return the event's action.
        :return: One of ('B', 'R', 'S') where B represents button press, R represents wheel rotation,
        and S represents swipe action.
        """
        return self._action

    @property
    def value(self):
        """
        Return the value related to event's action.
        :return: A string with either a numeric value such as '1' for button press or '0' for button release,
        a delta value such as '-4' or '42' for rotation action, or a single character such as 'U', 'D', 'L', or
        'R' to indicate swipe direction.
        """
        return self._value

    def __unicode__(self):
        return 'action: {}, value: {}'.format(self._action, self._value)


class NuimoEvent(object):
    """
    A higher-level representation of a Nuimo event.
    This class is essentially a structured way to store all the pertinent characteristics of an event as
    received form the Nuimo. This representation takes into account previous Nuimo states so it is possible
    to determine whether the button is down when the wheel is being rotated, for example.

    """
    ACTIONS = ('button_press', 'button_release', 'rotate', 'swipe')

    def __init__(self, action=None, button_pressed=False, button_exclusive=True,
                 rotate_delta=None, swipe_direction=None):
        if action not in self.ACTIONS:
            raise ValueError('action {} is not supported.'.format(action))
        self.action = action
        self.button_pressed = button_pressed
        # True if button release event was immediately preceded by button press, indicating no other events
        # during button press.
        self.button_exclusive = button_exclusive
        self.rotate_delta = rotate_delta
        self.swipe_direction = swipe_direction
        super(NuimoEvent, self).__init__()


class NuimoGlyph(object):
    """
    A single glyph designed to appear on the Nuimo's LED matrix.
    For now, this class supports only a small number of 'hard-coded' symbols,
    however it would be interesting to extend this to supporting arbitrary
    characters and symbols automatically generated from a font.
    The initial work on this has already been accomplished.
    """

    PLAY =  b'*        ' \
            b'***      ' \
            b'*****    ' \
            b'*******  ' \
            b'*********' \
            b'*******  ' \
            b'*****    ' \
            b'***      ' \
            b'*        '

    PAUSE = b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***' \
            b'***   ***'

    STOP =  b'         ' \
            b' ******* ' \
            b' ******* ' \
            b' ******* ' \
            b' ******* ' \
            b' ******* ' \
            b' ******* ' \
            b' ******* ' \
            b'         '

    SEEK_FORWARD = \
            b'*   *    ' \
            b'**  **   ' \
            b'*** ***  ' \
            b'******** ' \
            b'*********' \
            b'******** ' \
            b'*** ***  ' \
            b'**  **   ' \
            b'*   *    '

    SEEK_REVERSE = \
            b'    *   *' \
            b'   **  **' \
            b'  *** ***' \
            b' ********' \
            b'*********' \
            b' ********' \
            b'  *** ***' \
            b'   **  **' \
            b'    *   *'

    SKIP_FORWARD = \
            b'*   *   *' \
            b'**  **  *' \
            b'*** *** *' \
            b'*********' \
            b'*********' \
            b'*********' \
            b'*** *** *' \
            b'**  **  *' \
            b'*   *   *'

    SKIP_REVERSE = \
            b'*   *   *' \
            b'*  **  **' \
            b'* *** ***' \
            b'*********' \
            b'*********' \
            b'*********' \
            b'* *** ***' \
            b'*  **  **' \
            b'*   *   *'

    def __init__(self, char=None, symbol=None, vertical_fill_percent=None):
        """
        Initialize a glyph based on desired information it should display.
        :param char: Initialize from an arbitrary char, convert char to a 9x9 bitmap image and
        properly formatted string. Currently not supported.
        :param symbol: Initialize based on one of the pre-defined symbols, such as 'PLAY'.
        :param vertical_fill_percent: Initialize based on a percentage of vertical fill,
        where 0% is no columns lit, 50% is the bottom 4 columns lit, and 100% is all 9 columns lit.
        :return:
        """
        self.string = ''
        if char is not None:
            # generate a glyph from a character.
            raise NotImplementedError

        elif symbol is not None:
            if symbol not in ('PLAY', 'PAUSE', 'STOP', 'SEEK_FORWARD',
                              'SEEK_REVERSE', 'SKIP_FORWARD', 'SKIP_REVERSE'):
                raise ValueError('Symbol {} is not supported.'.format(symbol))
            self.string = getattr(self, symbol)

        elif vertical_fill_percent is not None:
            # generate a glyph with vertical fill based on a percentage specified.
            fill = min(100, max(0, vertical_fill_percent))
            colums_active = int(fill * 9.0 / 100.0)
            self.string = '         ' * (9 - colums_active) + '*********' * colums_active

        else:
            # empty glyph
            self.string = ' ' * 9 * 9
        super(NuimoGlyph, self).__init__()

    def _convert_char(self):
        """
        Experimental: convert a character to a 1-bit iamge to eventually
        generate a bitmap for arbitrary characters.
        :return:
        """
        # img = Image.new('1', (9, 9))
        # draw = ImageDraw.Draw(img)
        # # use a truetype font
        # #font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 8)
        # font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.dfont', 8)
        # draw.text((0, 0), self.char, font=font, fill=(1,))
        # return img

    def get_string(self):
        return self.string


class NuimoController(object):
    """
    A high-level abstraction for the Nuimo controller. Consumes RawNuimoEvent objects, updates internal
    state, and returns NuimoEvent objects representing updated state.

    """
    def __init__(self):
        self.states = {
            'button_pressed': False,
            'button_press_exclusive': True,
        }
        super(NuimoController, self).__init__()

    def consume_raw_event(self, raw_event):
        """
        Consume a RawNuimoEvent object, update internal state, and return a
        NuimoEvent object which represents the updated internal state.
        :param raw_event: The incoming RawNuimoEvent.
        :return: A NuimoEvent object which represents the updated internal state.
        """
        if raw_event.action == 'B':
            # Button press/release
            if raw_event.value == '1':
                self.states['button_pressed'] = True
                self.states['button_press_exclusive'] = True
                event = NuimoEvent(action='button_press', button_pressed=True)
            else:
                self.states['button_pressed'] = False
                event = NuimoEvent(
                    action='button_release',
                    button_pressed=False,
                    button_exclusive=self.states['button_press_exclusive']
                )

        elif raw_event.action == 'R':
            # Rotation
            self.states['button_press_exclusive'] = False
            event = NuimoEvent(
                action='rotate',
                rotate_delta=int(raw_event.value),
                button_pressed=self.states['button_pressed']
            )

        elif raw_event.action == 'S':
            # Swipe
            event = NuimoEvent(action='swipe', swipe_direction=raw_event.value)
        else:
            raise ValueError('unsupported event consumed: {}'.format(raw_event.action))
        return event


class MediaPlayerController(object):
    """
    A standard interface to the media player. Interfaces built on a specific
    protocol should inherit from this interface class.

    """
    def play(self):
        """
        Begin media file playback.
        :return:
        """
        raise NotImplementedError

    def stop(self):
        """
        Stop media file playback.
        :return:
        """
        raise NotImplementedError

    def pause(self):
        """
        Pause media playback.
        :return:
        """
        raise NotImplementedError

    def seek(self, seconds):
        """
        Seek forward/backward within current track.
        :param seconds: The number of seconds to seek forward/backward. Negative values
        are interpreted as seeking backward.
        :return:
        """
        raise NotImplementedError

    def skip_forward(self):
        """
        Skip forward to next item in media playback.
        :return:
        """
        raise NotImplementedError

    def skip_backward(self):
        """
        Skip backward to previous item in media playback.
        :return:
        """
        raise NotImplementedError

    def get_volume(self):
        """
        Return the current player volume level
        :return: Volume as a floating point number between 0 and 100
        """
        raise NotImplementedError

    def set_volume(self, volume):
        """
        Set the player volume level.
        :param volume: Volume as a floating point number between 0 and 100.
        :return:
        """
        raise NotImplementedError


class TelnetVLCController(MediaPlayerController):
    """
    A controller for VLC media player over Telnet interface
    """
    def __init__(self):
        self.connection = telnetlib.Telnet('localhost', 4212)
        self.connection.read_until('Password: ')
        self.connection.write(b'secret\n')
        print self.connection.read_until('>')
        super(TelnetVLCController, self).__init__()

    def _send_command(self, cmd):
        print('send_command: ', cmd)
        self.connection.write(cmd)
        return self.connection.read_until('>')

    def play(self):
        self._send_command(b'play\n')

    def pause(self):
        self._send_command(b'pause\n')

    def stop(self):
        self._send_command(b'stop\n')

    def seek(self, seconds):
        # TODO: This actually seeks in percent, seconds and ms seem to be broken in VLC telnet IF.
        self._send_command(b'seek {:+.3f}\n'.format(seconds))

    def skip_forward(self):
        self._send_command(b'next\n')

    def skip_backward(self):
        self._send_command(b'prev\n')

    def get_volume(self):
        res = self._send_command(b'volume\n')
        s = re.match(r'\D*(\d+)\r?\n', res).groups()[0]
        return float(s) / 3.2

    def set_volume(self, volume):
        self._send_command(b'volume {:d}\n'.format(int(volume * 3.2)))


class NuimoVLCController(object):
    """
    A stateful media controller object.
    """
    def __init__(self, player_interface):
        self.player_interface = player_interface

        self.player_states = {
            'playing': False
        }
        super(NuimoVLCController, self).__init__()

    def _button_release(self, event):
        if event.button_exclusive is not False:
            if self.player_states['playing'] is False:
                self.player_interface.play()
                self.player_states['playing'] = True
                return NuimoGlyph(symbol='PLAY')
            else:
                self.player_interface.pause()
                self.player_states['playing'] = False
                return NuimoGlyph(symbol='PAUSE')
        else:
            # clear display from whatever alternate mode was active
            return NuimoGlyph()

    def _rotate(self, event):
        if event.button_pressed:
            # seek forward and back
            scaled_delta = event.rotate_delta / 500.0
            self.player_interface.seek(scaled_delta)
            if scaled_delta > 0:
                return NuimoGlyph(symbol='SEEK_FORWARD')
            else:
                return NuimoGlyph(symbol='SEEK_REVERSE')
        else:
            # change volume
            scaled_delta = abs(event.rotate_delta / 16.0)
            volume = self.player_interface.get_volume()
            if event.rotate_delta > 0:
                volume += math.ceil(scaled_delta)
            else:
                volume -= math.ceil(scaled_delta)
            if volume > 100:
                volume = 100
            elif volume < 0:
                volume = 0
            self.player_interface.set_volume(volume)
            return NuimoGlyph(vertical_fill_percent=volume)

    def _swipe(self, event):
            # swipe
            print(event.swipe_direction)
            if event.swipe_direction == 'R':
                self.player_interface.skip_forward()
                self.player_states['playing'] = True
                return NuimoGlyph(symbol='SKIP_FORWARD')
            elif event.swipe_direction == 'L':
                self.player_interface.skip_backward()
                self.player_states['playing'] = True
                return NuimoGlyph(symbol='SKIP_REVERSE')
            elif event.swipe_direction == 'D':
                self.player_interface.stop()
                self.player_states['playing'] = False
                return NuimoGlyph(symbol='STOP')

    def consume_nuimo_event(self, event):
        """
        Consume a NuimoEvent object and perform the necessary control actions in the media player.
        :param event: The NuimoEvent object to consume.
        :return: A NuimoGlyph object to display on the device.
        """
        if event.action == 'button_release':
            glyph = self._button_release(event)
        elif event.action == 'rotate':
            glyph = self._rotate(event)
        elif event.action == 'swipe':
            glyph = self._swipe(event)
        else:
            glyph = None
        return glyph


def run_interface():
    """
    Main module entry point
    :return:
    """
    from websocket import create_connection

    ws = create_connection('ws://localhost:8086/')
    nuimo_controller = NuimoController()
    vlc_controller = NuimoVLCController(TelnetVLCController())

    try:
        while True:
            raw_event = RawNuimoEvent(ws.recv())
            print "Received '%s'" % raw_event
            nevent = nuimo_controller.consume_raw_event(raw_event)
            glyph = vlc_controller.consume_nuimo_event(nevent)
            if glyph is not None:
                ws.send(glyph.get_string())

    except KeyboardInterrupt:
        pass

    finally:
        ws.close()


if __name__ == '__main__':
    run_interface()

