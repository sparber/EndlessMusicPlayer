import pygtk
pygtk.require('2.0')
import gtk, gobject
from mplayer.gtk2 import GtkPlayerView
from youtube import youtube_search, getVideoUrl


PLAYLIST = """Shoby ft. Lilly Ahlberg - Outside (Original mix)
Pink Floyd - Wish you were here
Fountains of Wayne - Hey Julie
Ed Sheeran - I See Fire
""".split("\n")


#PLAYLIST = ["fountains of wayne - hey julie", "wish you were here - pink floyd", "acdc t.n.t."]


class PlayStatus(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
        self.set_size_request(20, 500)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        self.gc = None
        
        self.connect("expose-event", self.exposed)
        
        self.ypos = None
        
        self.initialized = False
    
    def exposed(self, *args):
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        #self.window.set_foreground(gtk.gdk.Color(green=65535))
        
        self.initialized = True
        
        self.drawPlay()
        return True
    
    def setPlayPos(self, ypos):
        self.ypos = ypos
        if self.initialized:
            self.drawPlay()
        
    def drawPlay(self):
        if self.ypos == None:
            return

        self.window.draw_polygon(self.gc, True, [(12, self.ypos-8), (20, self.ypos), (12, self.ypos+8)])



class Playlist(gtk.HBox):   
    def __init__(self, player):
        gtk.HBox.__init__(self)
        self.player = player
        self.current = -1
        
        self.playstatus = PlayStatus()
        self.pack_start(self.playstatus, expand=False, fill=False)
        self.playstatus.show()
        self.playstatus.connect("button-press-event", self.clicked)
        
        textbox = self.create_textbox()
        self.pack_start(textbox, expand=True, fill=True)
        textbox.show()

    def insert_text(self, buffer):
        iter = buffer.get_iter_at_offset(0)
        buffer.insert(iter, "\n".join(PLAYLIST))
    
    def create_textbox(self):
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.entry = gtk.TextView(buffer=None)
        self.textbuffer = self.entry.get_buffer()
        self.insert_text(self.textbuffer)
        scrolledwindow.add(self.entry)
        self.entry.show()
        return scrolledwindow
    
    def clicked(self, widget, event):
        if not (event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS):
            return False
        startiter = self.entry.get_iter_at_location(int(event.x), int(event.y))
        self.player.play(startiter.get_line())
        
        return True
    
    def get(self, index):
        self.current = index
        
        return self._get_text()
    
    def get_previous(self):
        self.current -= 1
        
        return self._get_text()
    
    def get_next(self):
        self.current += 1
        
        return self._get_text()
        
    def _get_text(self):
        startiter = self.textbuffer.get_iter_at_line(self.current)
        enditer = self.textbuffer.get_iter_at_line(self.current+1)
        
        text = self.textbuffer.get_text(startiter, enditer)
        
        pos = self.entry.get_iter_location(startiter)
        self.playstatus.setPlayPos(pos.y+pos.height/2)
        
        return text


class ControlButtons(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_BUTTON)
        self.prev = gtk.Button()
        self.prev.set_image(image)
        self.pack_start(self.prev)#, expand=True, fill=True)
        self.prev.show()

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.play = gtk.Button()
        self.play.set_image(image)
        self.pack_start(self.play)#, expand=True, fill=True)
        self.play.show()

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_NEXT, gtk.ICON_SIZE_BUTTON)
        self.next = gtk.Button()
        self.next.set_image(image)
        self.pack_start(self.next)#, expand=True, fill=True)
        self.next.show()


class Sidebar(gtk.VBox):
    def __init__(self, player):
        gtk.VBox.__init__(self)
        
        self.playlist = Playlist(player)
        self.pack_start(self.playlist, expand=True, fill=True)
        self.playlist.show()
        
        self.buttons = ControlButtons()
        self.buttons.prev.connect("clicked", player.play_previous)
        self.buttons.play.connect("clicked", player.playpause)
        self.buttons.next.connect("clicked", player.play_next)
        self.pack_start(self.buttons, expand=False, fill=True)
        self.buttons.show()
    
    def get(self, index):
        return self.playlist.get(index)
    
    def get_previous(self):
        return self.playlist.get_previous()
    
    def get_next(self):
        return self.playlist.get_next()



class Player(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        self.set_border_width(10)
        self.set_size_request(640, 480)
        self.set_title('EndlessMusicVideoPlayer')
        
        hpaned = gtk.HPaned()
        self.add(hpaned)
        hpaned.show()

        self.sidebar = Sidebar(self)
        hpaned.add1(self.sidebar)
        self.sidebar.show()
        
        self.mplayer = GtkPlayerView()
        hpaned.add2(self.mplayer)
        self.mplayer.show()
        
        self.mplayer.connect('eof', self.eof_reached)
        
        hpaned.set_position(250)
    
    def _play(self, text):
        videos, channels, playlists = youtube_search(text, 5)
        for video in videos:
            url = getVideoUrl(id=video[1])
            if url:
                self.mplayer.player.loadfile(url)
                break
    
    def playpause(self, *args):
        self.play_next()
    
    def play(self, index):
        text = self.sidebar.get(index)
        if text == None:
            return
        self._play(text)
    
    def eof_reached(self, widget, event):
        if event == 1:
            self.play_next()
    
    def play_previous(self, *args):
        text = self.sidebar.get_previous()
        if text == None:
            return
        self._play(text)
    
    def play_next(self, *args):
        text = self.sidebar.get_next()
        if text == None:
            return
        self._play(text)


queue = [
    "https://www.youtube.com/watch?v=3j8mr-gcgoI",
    "https://www.youtube.com/watch?v=YR5ApYxkU-U"
]

p = Player()
p.connect('destroy', lambda w: gtk.main_quit())
p.show()
#p.play_next()

gtk.main()





