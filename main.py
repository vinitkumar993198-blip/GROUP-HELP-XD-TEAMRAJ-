from fastapi import FastAPI, Query
import yt_dlp

app = FastAPI()

def search_youtube(query):
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "default_search": "ytsearch1"
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return {
            "title": info["title"],
            "url": info["url"],  # direct audio link
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail")
        }

@app.get("/search")
def search_song(title: str = Query(...)):
    data = search_youtube(title)
    return {"results": [data]}
