from apiclient.discovery import build
from apiclient.errors import HttpError
from subprocess import Popen, PIPE

from settings import DEVELOPER_KEY

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"



def getVideoUrl(url=None, id=None):
    if url == None:
        url = "https://youtube.com/watch?v=%s" % id
    
    proc = Popen(["quvi", "-vm", url, "--exec", "echo %u"], stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    return out


def youtube_search(query, max_results=1):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=max_results
    ).execute()

    videos = []
    channels = []
    playlists = []

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append((search_result["snippet"]["title"], search_result["id"]["videoId"]))
        elif search_result["id"]["kind"] == "youtube#channel":
            channels.append((search_result["snippet"]["title"], search_result["id"]["channelId"]))
        elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append((search_result["snippet"]["title"], search_result["id"]["playlistId"]))
    
    return videos, channels, playlists



