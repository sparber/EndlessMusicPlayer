import core# import Fetcher, FETCHER, TO_FETCH, Media
from settings import DEVELOPER_KEY
import providers.proxy
from thread import start_new_thread

from apiclient.discovery import build
from apiclient.errors import HttpError

from subprocess import Popen, PIPE



YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YoutubeMedia(core.Media):
    
    def __init__(self, search_result, displaytext=None):
        self.search_result = search_result
        self.id = search_result["id"]["videoId"]
        self.title = search_result["snippet"]["title"]
        #self.thumbnailUrl = search_result["snippet"]["thumbnail"]["medium"]["url"]
        
        core.Media.__init__(self, displaytext if displaytext != None else self.title)
    
    def __str__(self):
        return "%s {youtube: %s}" % (core.Media.__str__(self), self.id)
    
    def fetchStreamUrl(self, callback=None, args=(), schedule="now"):
        core.fetch("youtube", "stream", {"id": self.id}, self.setStreamUrl, (callback, args), schedule)
    
    def fetchSuggestions(self, callback=None, args=(), schedule="now"):
        core.fetch("youtube", "search", {"relatedToVideoId": self.id}, self.setSuggestions, (callback, args), schedule)
    
    def fetchThumbnail(self, callback=None, args=(), schedule="now"):
        core.fetch("youtube", "content", {"url": self.thumbnailUrl}, self.setThumbnail, (callback, args), schedule)


class YoutubeFetcher(core.Fetcher):

    PROVIDER_IDS = ["youtube"]
    ABILITIES = ["stream", "search"]
    
    def __init__(self):
        self.youtube = None
    
    def connect(self):
        if self.youtube == None:
            self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
            self.server = providers.proxy.TheServer("localhost", 9090)
            start_new_thread(self.server.main_loop, ())

    def fetch_autocomplete(self, query):
        content = cls.fetchContent("http://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q="+query)
        return content
    
    def fetch_stream(self, url=None, id=None):
        if url == None:
            url = "https://youtube.com/watch?v=%s" % id
            
        #proc = Popen(["quvi", "--category", "http", "-vm", url, "--exec", "echo %u"], stdout=PIPE, stderr=PIPE)
        #proc = Popen(["quvi", "-vm", "-e-v", url, "--exec", "echo %u"], stdout=PIPE, stderr=PIPE)
        proc = Popen(["youtube-dl", "-g", url], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        
        if out.startswith("https://"):
            out = "http://localhost:9090/"+out
        return out
        

    def fetch_search(self, **args):
        
        args.setdefault("callback", YoutubeMedia)
        callback = args.pop("callback")
        
        query = {
            "part": "id,snippet",
            "type": "video",
            "maxResults": 5,
        }
        query.update(args)
        
        search_response = self.youtube.search().list(**query).execute()

        items = []

        for search_result in search_response.get("items", []):
            items.append(callback(search_result, query.get("q", None)))
        
        return items


core.FETCHERS.insert(0, YoutubeFetcher())


