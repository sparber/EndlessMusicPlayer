from gui import Player
import core
import providers.youtube

import pygtk
pygtk.require('2.0')
import gtk, gobject


PLAYLIST = [
    "of monsters and men - dirty paws",
    "pink floyd - echoes space",
    "Shoby ft. Lilly Ahlberg - Outside (Original mix)",
    #"Pink Floyd - Wish you were here",
    #"Fountains of Wayne - Hey Julie",
    #"Ed Sheeran - I See Fire",
]


gobject.threads_init()


controller = core.Controller()
controller.start()


player = Player(controller)
player.connect('destroy', lambda w: gtk.main_quit())
player.show()
#p.play_next()

controller.setView(player)
controller.setPlaylist(PLAYLIST)

gobject.timeout_add(100, controller.update)

gtk.main()


controller.shutdown()



