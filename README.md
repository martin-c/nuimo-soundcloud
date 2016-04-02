## Control your Soundcloud player from the Nuimo ##

This repo demos how to control SoundCloud using a Senic Nuimo device, using the Nuimo web socket server, VLC and the SoundCloud API. 

We us the following Python libraries 
 * SoundCloud API wrapper https://github.com/soundcloud/soundcloud-python
 * Websocket client: https://pypi.python.org/pypi/websocket-client/
 * VLC Python bindings: https://github.com/oaubert/python-vlc (which require a locally installed VLC player)

To interact with the Nuimo device, we use the web socket server provided by Senic: https://github.com/getsenic/nuimo-websocket-server-osx

To use the SoundCloud examples, you need an API key (CLIENT ID), which needs to be set as an environment variable `CLIENT_ID`. You can get that at http://soundcloud.com/you/apps/new

To get the VLC integration to work, you might need to set a `VLC_PLUGIN_PATH` environment variable, see https://www.vlchelp.com/install-vlc-media-player-addon/ for the right options for different platforms (e.g. on Mac OSX it is `/Applications/VLC.app/Contents/MacOS/`). Do this if you see the error: `core libvlc error: No plugins found! Check your VLC installation.`
