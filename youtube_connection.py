import os
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import time

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
api_service_name = "youtube"
api_version = "v3"
# https://medium.com/mcd-unison/youtube-data-api-v3-in-python-tutorial-with-examples-e829a25d2ebd

order = "viewCount"

keys = pd.read_csv("keys.csv").key.tolist()

class YtConnection:
    key_counter = 0
    current_key = keys[0]
    youtube = None
    recurssion = 0

    def __init__(self):
        self.youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = self.current_key)

    def GetSearch(self, nextToken, search_term):
        srch = search_term + " gameplay"
        if (nextToken == ""):
            request = self.youtube.search().list(
                    part="id,snippet",
                    type='video',
                    q=srch,
                    order=order,
                    publishedAfter="2023-10-01T00:00:00Z",
                    maxResults=1000,
                    fields="nextPageToken,items(id(videoId),snippet(publishedAt,channelId,channelTitle,title,description))"
            )
        else:
            request = self.youtube.search().list(
                    part="id,snippet",
                    type='video',
                    q=srch,
                    order=order,
                    publishedAfter="2023-10-01T00:00:00Z",
                    maxResults=1000,
                    fields="nextPageToken,items(id(videoId),snippet(publishedAt,channelId,channelTitle,title,description))",
                    pageToken=nextToken
            )
        return request.execute()

    def GetViews(self, vidId):
        r = self.youtube.videos().list(
            part="statistics,contentDetails",
            id=vidId,
            fields="items(statistics,contentDetails(duration))"
        ).execute()
        return r

    def ExecuteRequest(self, type, vidId="", search_term="", nextToken=""):
        try:
            if type == "search":
                response = self.GetSearch(nextToken, search_term)
            if type == "views":
                response = self.GetViews(vidId)

            self.recurssion = 0
        except Exception as error:
            print("An exception occurred 1:", error)
            self.recurssion += 1
            time.sleep(0.1)
            if (self.recurssion > 2):
                self.GetNextKey()
                self.youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = self.current_key)
            response = self.ExecuteRequest(type, vidId, search_term, nextToken)

        return response

    def GetNextKey(self):
        self.key_counter += 1
        self.current_key = keys[self.key_counter]

