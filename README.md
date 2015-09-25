# EndlessMusicPlayer

**Attention: this is a very early version and it does not work properly**

The central idea is to have a textbox as playlist were you can type anything or paste anything and each line is interpreted as song, which is then streamed over a popular video streaming service. 

Dependencies
===========

- Python2 (the player is written in Python)
- gtk2 and pygtk (used for the GUI)
- mplayer and python-mplayer (used for playing the media)
- google-api-python-client (used for searching the songs)
- youtube-dl (used for fetching the media url)

Enjoy & have fun!

**Note that currently in order to make it work you need to create a file called settings.py with the string constant DEVELOPER_KEY in it. This must be a valid Google API key**


