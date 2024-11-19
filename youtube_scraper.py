import os
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import time
import re

from youtube_connection import *
from db_interface import *

ytc = YtConnection()

def FilterIrrelevant(tmp, regex):
    tmp['key_desc'] = True
    tmp['key_title'] = True
    tmp['key_desc'] = tmp['key_desc'] * tmp['desc'].str.contains(regex.lower(), case=False)
    tmp['key_title'] = tmp['key_title'] * tmp['title'].str.contains(regex.lower(), case=False)
        
    tmp['keep'] = tmp['key_desc'] + tmp['key_title']
    return tmp

def ResponseToPD(response):
    dict = {"channel":[], "title":[], "desc":[], "id": []}
    for i in range(len(response['items'])):
        dict["channel"].append(response['items'][i]['snippet']['channelTitle'])
        dict["title"].append(response['items'][i]['snippet']['title'])
        dict["desc"].append(response['items'][i]['snippet']['description'])
        dict["id"].append(response['items'][i]['id']['videoId'])
    return pd.DataFrame(dict)

def GetYTVideos(ytc, search_term):
    cont = True
    nextToken = ""
    vids = pd.DataFrame()
    j = 0

    reg = re.sub("[^a-zA-Z0-9]+", "[^a-zA-Z0-9]+", search_term.lower())
    while cont:
        time.sleep(0.1)
        response = ytc.ExecuteRequest("search", search_term=search_term, nextToken=nextToken)
        
        tmp = ResponseToPD(response)
        if (tmp.shape[0] == 0):
            if (vids.shape[0]==0):
                vids = tmp
            break
        tmp = FilterIrrelevant(tmp, reg)
        vids = pd.concat([vids, tmp])

        print(search_term + " iteration %s, rows: %s, pct: %s" % (j, tmp.shape[0], round(tmp.keep.mean(), 2)))

        try:
            nextToken = response['nextPageToken']
        except Exception as error:
            print("An exception occurred 2:", error)
            break

        cont = tmp.keep.mean() > 0.3
        j = j+1
        if (j > 20):
            cont = False
    
    vids = vids[vids.keep].reset_index(drop=True)
    vids['game'] = search_term
    SaveVideos(vids)

    return vids

def GetYTViews(ytc, vids, status, status_string):
    vids['duration'] = 0
    vids['views'] = 0
    for i in range(vids.shape[0]):
        if i % 200 == 0:
            status = f"Downloading views... {i} / {vids.shape[0]}"
            status_string.set(status)

        # Getting the id
        time.sleep(0.1)
        vidId = vids.id[i]
        # Getting stats of the video
        r = ytc.ExecuteRequest("views", vidId=vidId)

        try:
            duration = DurationStringToHours(r['items'][0]['contentDetails']['duration'])
            views = 0
            if ("viewCount" in r['items'][0]['statistics']):
                views = r['items'][0]['statistics']['viewCount']
            UpdateViews(vidId, duration, views)
        except Exception as error:
            print("An exception occurred 3:", error)
            print(r)

    return vids

def DurationStringToHours(duration):
    # Remove 'PT' from the string
    duration = re.sub("PT", "", duration)

    # Extract hours, minutes, and seconds
    hours = re.sub("H.*", "", re.sub(".*?(\\d+)H.*", "\\1", duration))
    minutes = re.sub("M.*", "", re.sub(".*?(\\d+)M.*", "\\1", duration))
    seconds = re.sub("S.*", "", re.sub(".*?(\\d+)S.*", "\\1", duration))

    # Convert extracted values to numbers, replace None with 0
    hours = float(hours) if hours.isdigit() else 0
    minutes = float(minutes) if minutes.isdigit() else 0
    seconds = float(seconds) if seconds.isdigit() else 0

    # Calculate total duration in hours
    total_hours = hours + minutes / 60 + seconds / 3600
    return total_hours
