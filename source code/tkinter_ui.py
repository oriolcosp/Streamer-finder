from tkinter import *
import pandas as pd
import sqlite3
import os.path

from youtube_scraper import *
from db_interface import *
from youtube_connection import *
from merge_yt_twitch import *

# https://realpython.com/python-gui-tkinter/
# https://medium.com/@fareedkhandev/modern-gui-using-tkinter-12da0b983e22
# https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/

# pyinstaller.exe --onefile -w tkinter_ui.py
con = sqlite3.connect('app.db')

root = Tk()
root.title("Streamer finder")
root.geometry("800x800")

status_string = StringVar(value="")
status = ""

inst_text = """
    Create a file named 'games.csv' with a list of games you want to scrap
    separated by line breaks (enter) on the same folder as the program.
    Then click the import games button.
"""

scrap_text = """
    Check the imported games are correct.
    If they are, click the "Download YT" button to start downloading YT viewership data
    for the selected games. This will take a while if the data hasn't been downloaded yet.
    Unless the message "Scraping done" appears at the end, the scraping will not
    have finished (insuficient keys), and will need to be run again in 24h.
"""

merge_text = """
    The youtube data is already downloaded.
    Now you need to create a folder named "twitch" in the same folder as the exe,
    and download all the data from sully gnome for your target games.
    Click the "Create file" button to create a file with the list of streamers and
    their statistics.
    Once you have the file, update the streamer_emails.csv file to get the statistics
    with the emails".
"""

instructions = StringVar(value=inst_text)

instructionsLabel = Label(root, textvariable=instructions)
instructionsLabel.pack(pady=10)

def importGames():
    if (os.path.isfile("games.csv")):
        games = pd.read_csv("games.csv", names=["title"])
        status_string.set("Imported games:\n" + "\n".join(games.title.tolist()))
        instructions.set(scrap_text)
    else:
        status_string.set("<no games imported yet>")

importGames()

importGamesButton = Button(root, text="Import games", command=importGames)
importGamesButton.pack(padx=10, pady=10)

ytc = YtConnection()

def scrapYTGames():
    status = ""
    already_scraped = GetAlreadyScraped().game.tolist()
    games = pd.read_csv("games.csv", names=["title"])
    for game in games.title.tolist():
        if (game in already_scraped):
            status += "\nAlready scraped " + game
            status_string.set(status)
        else:
            status += "\nScraping " + game
            status_string.set(status)
            vids = GetYTVideos(ytc, game)

    pendingViews = GetPendingViews()
    status = f"Downloading views... 0 / {pendingViews.shape[0]} pending videos"
    status_string.set(status)
    GetYTViews(ytc, pendingViews, status, status_string)
    status += f"\nScraping done"
    status_string.set(status)
    instructions.set(merge_text)


scrapYTGamesButton = Button(root, text="Download YT", command=scrapYTGames)
scrapYTGamesButton.pack(padx=10, pady=10)

def make_file():
    twitch = process_twitch()
    yt = get_youtube()
    channel_game = merge_yt_twitch(twitch, yt)
    channel_game.to_csv("streamer_list.csv", index=False)
    status_string.set("File created at streamer_list.csv")


makeFileButton = Button(root, text="Create file", command=make_file)
makeFileButton.pack(padx=10, pady=10)

statusLabel = Label(root, textvariable=status_string)
statusLabel.pack(pady=10)

root.mainloop()

