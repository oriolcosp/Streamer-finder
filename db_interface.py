import sqlite3
import pandas as pd

VIDEO_TABLE = "videos"
con = sqlite3.connect('app.db')

def SaveVideos(videos):
    if (not "duration" in videos.columns):
        videos['duration'] = 0
        videos['views'] = 0
    videos.to_sql(VIDEO_TABLE, con, if_exists="append", index=False)

def GetVideos():
    return pd.read_sql_query(f"SELECT * from {VIDEO_TABLE}", con)

def GetPendingViews():
    return pd.read_sql_query(f"SELECT * from {VIDEO_TABLE} where duration = 0", con)

def UpdateViews(vId, duration, views):
    query = f"UPDATE {VIDEO_TABLE} SET duration = {duration}, views = {views} WHERE id = '{vId}'"
    con.cursor().execute(query)
    con.commit()

def GetAlreadyScraped():
    try:
        return pd.read_sql_query(f"SELECT distinct game as game from {VIDEO_TABLE}", con)
    except:
        return pd.DataFrame(columns = ["game"])
