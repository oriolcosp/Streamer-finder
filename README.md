# Streamer-finder
A tool to find content creators who played games from a list.

## Description
I built this tool to easily find content creators from Twitch and YouTube who could play my games.
It takes as inputs a list of games (plus the sullygnome data for those games), and returns a csv file with a row for each streamer who played any of those games on Twitch or YouTube and some statistics like the number of stream hours, average viewers, list of the games played, ... It does not automatically get the emails of those content creators, that has to be done manually (or outsourced to fiverr).
Internally, it queries the YouTube API for the names of the games, saves the videos and statistics on an internal database, merges the data with Twitch data, and finally processes everything to have analytics at the channel level.

## Using the tool
Follow these steps:
### Populate the keys.csv file
The keys.csv file should contain one YouTube API key per row. The current one won't work, it's there as an example of the format of those keys.

5 keys should be enough to get data for 10 games in one go. The tool runs through each key until it reaches the daily limit of queries and jumps through the next. If you're in a hurry just get more keys.

[Here's how to get your keys (section "How to get an API key" near the top)](https://medium.com/mcd-unison/youtube-data-api-v3-in-python-tutorial-with-examples-e829a25d2ebd).
### Populate the games.csv file
The games.csv contains the names of the games you want to search, one per row.

The names should be the same as on the Twitch folder (next section), although the tool does some fuzzy matching.

The tool sometimes gets results wrong when searching for relatively common words. This is because it's just searching those names on YouTube and sometimes gets confused. For example, when searching for the game "Shotgun King" I got many results from FPS games.

### Populate the Twitch folder
If you want the output file to also have Twitch data, you should populate this folder with the sullygnome files for all the games you're considering.

Go to [sullygnome.com](https://sullygnome.com/), type the name of the game you want on the search box (top right), click most watched, and select a period of time (I usually go for 365 days). Then click the "csv" button to download the top results. Usually, the first page will be enough, but if it's a very popular game you can download multiple pages.

Leave those files with their default names and move them to the "twitch" folder.

If you no longer want those games to appear on the tool, you should delete their files.

### Run the program
Run the "tkinter_ui.exe" file to run the program. It takes a while to start.

It should import the games file automatically.

Click the "Download YT" button to download the YT data for the games, the program will tell you whether it's done or not. If you previously downloaded data for a game it will skip it, to fix this you should delete the app.db file (which deletes all data) or use SQLite to delete the rows concerning that game.

Finally, click the "Create File" button and a "streamer list.csv" file should appear in the same folder. You should be able to easily open that with Excel and sort and filter streamers to find which are more suitable for your game. You may encounter problems with the numeric format but those can be solved within Excel.

## Conclusion
I'm not actively developing this tool, as my focus is on making games. If I encounter a bug while using it I'll probably fix it and upload it, but I probably won't be addressing any bug reports.

If someone wants to develop the tool further, contact me.

For advanced use, I've included the source code in python.
