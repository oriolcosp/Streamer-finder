# Streamer-finder
This repository contains the source code for the streamer-finder tool, you can use it to get intermediate results or improve the tool.
If you're looking for the tool itself, [you can find it here](https://oriolcosp.com/a-tool-to-find-content-creators-who-played-games-from-a-list/).

## Description
I built this tool to easily find content creators from Twitch and YouTube who could play my games.
It takes as inputs a list of games (plus the sullygnome data for those games), and returns a csv file with a row for each streamer who played any of those games on Twitch or YouTube and some statistics like the number of stream hours, average viewers, list of the games played, ... It does not automatically get the emails of those content creators, that has to be done manually (or outsourced to fiverr).
Internally, it queries the YouTube API for the names of the games, saves the videos and statistics on an internal database, merges the data with Twitch data, and finally processes everything to have analytics at the channel level.

