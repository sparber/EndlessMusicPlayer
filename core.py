import threading
import pygtk
pygtk.require('2.0')
import gtk, gobject
import time

from thread import start_new_thread



FETCHERS = []
TO_FETCH = []


class Media(object):
    
    CHILDREN = []
    
    def __init__(self, displaytext):
        self.displaytext = displaytext
        
        self.title = None
        
        self.stream = None
        self.suggestions = None
        self.thumbnail = None
    
    def __str__(self):
        return self.displaytext
    
    def getDisplayText(self):
        return self.displaytext
        
    def fetchStreamUrl(self, callback=None, args=(), schedule="now"):
        raise RuntimeError("method not implemented")
    
    def fetchSuggestions(self, callback=None, args=(), schedule="now"):
        raise RuntimeError("method not implemented")
    
    def fetchThumbnail(self, callback=None, args=(), schedule="now"):
        raise RuntimeError("method not implemented")
    
    def setStreamUrl(self, url, callback=None, args=()):
        self.stream = url
        if callback != None:
            callback(*args)
    
    def getStreamUrl(self):
        return self.stream
    
    def setSuggestions(self, videos, callback=None, args=()):
        self.suggestions = videos
        if callback != None:
            callback(*args)
    
    def getSuggestions(self):
        return self.suggestions
    
    def setThumbnail(self, data, callback=None, args=()):
        self.thumbnail = data
        if callback != None:
            callback(*args)
    
    def getThumbnail(self):
        return self.thumbnail

class NoResult(Media):
    def __str__(self):
        return "%s {any: none}" % Media.__str__(self)


class MediaPool(object):
    def __init__(self):
        pass
    
    def getMedia(self, line, callback, args):
        videos = fetch("any", "search", {"q": line}, self.callback, (callback, args), "last")
    
    def callback(self, results, callback, args):
        results[0].fetchStreamUrl(self.callbackStreams, (results, callback, args), "next")
    
    def callbackStreams(self, results, callback, args):
        if results[0].getStreamUrl():
            callback(results[0], *args)
        elif len(results) > 1:
            results[1].fetchStreamUrl(self.callbackStreams, (results[1:], callback, args), "next")
        else:
            callback(NoResult(results[0].getDisplayText()), *args)
        


class Fetcher(object):
    PROVIDER_IDS = []
    ABILITIES = []
    
    def connect(self):
        pass


SCHEDULE_NOW = "now"
SCHEDULE_LAST = "last"
SCHEDULE_NEXt = "next"


def fetch(provider_id, fetch_type, f_args, callback=None, c_args=(), schedule="now"):
    for fetcher in FETCHERS:
        fetcher.connect()
    
    if schedule == "next":
        TO_FETCH.insert(0, (provider_id, fetch_type, f_args, callback, c_args))
        #start_new_thread(fetch, (provider_id, fetch_type, f_args, callback, c_args, "now"))
        return
    elif schedule == "last":
        TO_FETCH.append((provider_id, fetch_type, f_args, callback, c_args))
        #start_new_thread(fetch, (provider_id, fetch_type, f_args, callback, c_args, "now"))
        return
    
    print provider_id, fetch_type, f_args
    
    for fetcher in FETCHERS:
        
        if not (provider_id == "any" or "any" in fetcher.PROVIDER_IDS or provider_id in fetcher.PROVIDER_IDS):
            continue
        
        if fetch_type not in fetcher.ABILITIES:
            continue
        
        fetch_method = getattr(fetcher, "fetch_%s" % fetch_type)
        if callback != None:
            callback(fetch_method(**f_args), *c_args)
        else:
            return fetch_method(**f_args)



class Playlist(object):
    def __init__(self, controller):
        self.playlist = []
        self.current = 0
        self.controller = controller
    
    def setContent(self, content):
        self.playlist = []
    
        for index,line in enumerate(content):
            self.playlist.append(None)
            self.updateLine(line, index)
    
    def getContent(self):
        return self.playlist
    
    def updateLine(self, line, index):
        self.controller.to_update.append(("playlist", (index, line)))
        if type(line) == str:
            short = line.strip()
            if short.startswith("#") or not short:
                self.playlist[index] = None
                return
            
            self.playlist[index] = line
            media = self.controller.pool.getMedia(line, self.updateLine, (index,))
        
        else:
            self.playlist[index] = line

    
    def moveTo(self, index):
        self.current = index-1
        self.moveNext()
    
    def moveNext(self):
        self.current += 1
        while self.current < len(self.playlist) and not self.playlist[self.current]:
            self.current += 1
    
    def movePrevious(self):
        self.current -= 1
        while self.current > 0 and not self.playlist[self.current]:
            self.current -= 1

    def getCurrentIndex(self):
        return self.current

    def getMedia(self, index=None):
        if index == None:
            index = self.current
        if 0 <= index < len(self.playlist):
            return self.playlist[index]
        else:
            return None
    

class Controller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._shutdown = False
        
        self.to_update = []
        
        self.pool = MediaPool()
        
        self.playing = False
        self.playlist = Playlist(self)
    
    def setView(self, view):
        self.view = view
    
    def setPlaylist(self, playlist):
        self.playlist.setContent(playlist)
    
    def getPlaylist(self):
        return self.playlist
    
    def jump_next(self, play=True):
        self.playlist.moveNext()
        if play:
            self.play()
        else:
            self.playing = False
            self.to_update.append(("status", ("pause", self.playlist.getCurrentIndex())))
    
    def jump_previous(self, play=True):
        self.playlist.movePrevious()
        if play:
            self.play()
        else:
            self.playing = False
            self.to_update.append(("status", ("pause", self.playlist.getCurrentIndex())))
    
    def jump_to(self, index, play=True):
        self.playlist.moveTo(index)
        if play:
            self.play()
        else:
            self.playing = False
            self.to_update.append(("status", ("pause", self.playlist.getCurrentIndex())))
    
    def playpause(self):
        self.playing = not self.playing
        if self.playing:
            self.play()
        else:
            self.playing = False
            self.to_update.append(("status", ("pause", self.playlist.getCurrentIndex())))
    
    def play(self):
        if not self.playing:
            self.playing = True
            self.to_update.append(("status", ("play", self.playlist.getCurrentIndex())))
        media = self.playlist.getMedia()
        self.view.play(media.getStreamUrl())
    
    def update(self):
        self.view.update(self.to_update)
        self.to_update = []
        return True
    
    def shutdown(self):
        self._shutdown = True

    def run(self):
        while not self._shutdown:
            while not TO_FETCH:
                time.sleep(0.01)
                if self._shutdown:
                    return
            
            fetch(*TO_FETCH.pop(0))




