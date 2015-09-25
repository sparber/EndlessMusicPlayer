import pygtk
pygtk.require('2.0')
import gtk, gobject
from mplayer.gtk2 import GtkPlayerView
import core


class MediaPicker(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
        #self.set_size_request()


class PlayStatus(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
        self.set_size_request(20, 500)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        self.gc = None
        
        self.foreground = self.get_colormap().alloc(0x0000, 0xFFFF, 0x0000)

        self.background = self.get_colormap().alloc(0x0000, 0x0000, 0x0000)

        
        self.connect("expose-event", self.exposed)
        
        self.ypos = None
        
        self.initialized = False
    
    def update(self, what):
        if what != None:
            self.setPlayPos(what[1])
    
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
        x, y, width, height = self.get_allocation()
        self.gc.foreground = self.background
        self.window.draw_rectangle(self.gc, True, 0, 0, width, height)
        self.gc.foreground = self.foreground
    
        if self.ypos == None:
            return

        self.window.draw_polygon(self.gc, True, [(12, self.ypos-8), (20, self.ypos), (12, self.ypos+8)])


class Playlist(gtk.HBox):
    def __init__(self, controller):
        gtk.HBox.__init__(self)
        
        self.controller = controller
        
        self.playstatus = PlayStatus()
        self.pack_start(self.playstatus, expand=False, fill=False)
        self.playstatus.show()
        self.playstatus.connect("button-press-event", self.clicked)
        
        textbox = self.create_textbox()
        self.pack_start(textbox, expand=True, fill=True)
        textbox.show()
    
    def updatePlaylist(self, what):
        if what == None:
            print "NOT IMPLEMENTED"
            #playlist = self.controller.getPlaylist().getContent()
            #self.insert_text("\n".join([str(x) for x in playlist])+"\n")
        else:
            self.insert_text(*what)
            
    
    def update(self, update):
        if update[0] == "playlist":
            self.updatePlaylist(update[1])
        elif update[0] == "status":
            self.playstatus.update(update[1])

    def insert_text(self, index, line):
        if self.textbuffer.get_line_count() <= index+1:
            end = self.textbuffer.get_end_iter()
            self.textbuffer.insert(end, "\n"*(index+2 - self.textbuffer.get_line_count()))
        start = self.textbuffer.get_iter_at_line(index)
        end = self.textbuffer.get_iter_at_line(index+1)
        
        self.textbuffer.delete(start, end)
        
        self.textbuffer.insert(start, str(line)+"\n")
        
    
    def create_textbox(self):
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.entry = gtk.TextView(buffer=None)
        self.textbuffer = self.entry.get_buffer()
        self.textbuffer.connect("notify::cursor-position", self.on_cursor_position_changed)

        scrolledwindow.add(self.entry)
        self.entry.show()
        return scrolledwindow
    
    def on_cursor_position_changed(self, buffer, data=None):
        #print "--", buffer.props.cursor_position
        pass
    
    def clicked(self, widget, event):
        if not (event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS):
            return False
        startiter = self.entry.get_iter_at_location(int(event.x), int(event.y))
        self.controller.jump_to(startiter.get_line())
        
        return True
    
    #def _get_text(self):
    #    startiter = self.textbuffer.get_iter_at_line(self.current)
    #    enditer = self.textbuffer.get_iter_at_line(self.current+1)
    #    
    #    text = self.textbuffer.get_text(startiter, enditer)
    #    
    #    pos = self.entry.get_iter_location(startiter)
    #    self.playstatus.setPlayPos(pos.y+pos.height/2)
    #    
    #    return text


class ControlButtons(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_BUTTON)
        self.prev = gtk.Button()
        self.prev.set_image(image)
        self.pack_start(self.prev)
        self.prev.show()

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.play = gtk.Button()
        self.play.set_image(image)
        self.pack_start(self.play)
        self.play.show()

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_NEXT, gtk.ICON_SIZE_BUTTON)
        self.next = gtk.Button()
        self.next.set_image(image)
        self.pack_start(self.next)
        self.next.show()


class Sidebar(gtk.VBox):
    def __init__(self, controller):
        gtk.VBox.__init__(self)
        
        self.controller = controller
        
        self.playlist = Playlist(controller)
        self.pack_start(self.playlist, expand=True, fill=True)
        self.playlist.show()
        
        self.buttons = ControlButtons()
        self.buttons.prev.connect("clicked", lambda x: controller.jump_previous())
        self.buttons.play.connect("clicked", lambda x: controller.playpause())
        self.buttons.next.connect("clicked", lambda x: controller.jump_next())
        self.pack_start(self.buttons, expand=False, fill=True)
        self.buttons.show()
    
    def update(self, update):
        self.playlist.update(update)



class Player(gtk.Window):
    def __init__(self, controller):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        self.controller = controller
        
        self.set_border_width(10)
        self.set_size_request(640, 480)
        self.set_title('EndlessMusicVideoPlayer')
        
        hpaned = gtk.HPaned()
        self.add(hpaned)
        hpaned.show()

        self.sidebar = Sidebar(controller)
        hpaned.add1(self.sidebar)
        self.sidebar.show()
        
        vpaned = gtk.VPaned()
        hpaned.add2(vpaned)
        vpaned.show()
        
        self.picker = MediaPicker()
        vpaned.add1(self.picker)
        self.picker.show()
        
        self.mplayer = GtkPlayerView()
        vpaned.add2(self.mplayer)
        self.mplayer.show()
        #self.mplayer.player.avformat_network_init()
        
        self.mplayer.connect('eof', self.eof_reached)
        
        vpaned.set_position(250)
        hpaned.set_position(250)
    
    def update(self, to_update):
        for update in to_update:
            if update[0] in ("status", "playlist"):
                self.sidebar.update(update)
            else:
                raise RuntimeError("unknown update")
    
    def play(self, url):
        self.mplayer.player.loadfile(url)
    
    def eof_reached(self, widget, event):
        if event == 1:
            self.controller.jump_next(True)
    


