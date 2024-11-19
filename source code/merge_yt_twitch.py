import pandas as pd
import os
import re
from db_interface import *
import nltk

def clean_names(df):
    # Remove columns containing 'V'
    df = df.loc[:, ~df.columns.str.contains('V')]
    # Replace spaces with underscores and remove non-alphanumeric characters except underscores
    df.columns = [re.sub('[^a-z_]', '', col.lower().replace(' ', '_')) for col in df.columns]
    return df

def load_all_files(folder):
    streamer_files = [f for f in os.listdir(folder) if f.endswith('.csv')]  # List CSV files
    dt = pd.DataFrame()  # Empty DataFrame
    for f in streamer_files:
        game = f.split(" - ")[0]
        tmp = pd.read_csv(os.path.join(folder, f))
        tmp['game'] = game  # Create a column with the name of the game
        dt = pd.concat([dt, tmp], ignore_index=True)  # Append the game data to the big table
    dt = clean_names(dt)
    return dt

def process_twitch():
    dt = load_all_files("twitch")
    # Convert minutes to hours
    dt['watch_time_hours'] = dt['watch_time_mins'] / 60
    dt['stream_time_hours'] = dt['stream_time_mins'] / 60

    return dt

def load_all_files(folder):
    streamer_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    dt = pd.DataFrame()
    for f in streamer_files:
        game = f.split(" - ")[0]
        tmp = pd.read_csv(os.path.join(folder, f))
        tmp['game'] = game
        dt = pd.concat([dt, tmp], ignore_index=True)
    dt = clean_names(dt)
    return dt

def clean_names(df):
    df.columns = [re.sub('[^a-z_]', '', col.lower().replace(' ', '_')) for col in df.columns]
    return df

def get_youtube():
    dt = GetVideos()
    # https://www.researchgate.net/figure/Left-Average-percentage-viewed-of-a-video-versus-video-length-measured-in-minutes_fig3_343355041
    dt['stream_time_hours'] = dt['duration']
    dt['watch_time_hours'] = (20 / (dt['duration'] + 30) + 0.05).clip(lower=.1, upper=1) * dt['views']
    
    return dt

def fix_game_names(twitch, yt):
    twitch["game"] = twitch.game.str.lower().replace("[^a-z0-9 ]", "").str.strip()
    yt["game"] = yt.game.str.lower().replace("[^a-z0-9 ]", "").str.strip()

    games = pd.read_csv("games.csv", names=["game"])
    names = pd.DataFrame({"game2": twitch.game.unique().tolist() + yt.game.unique().tolist()})
    names = names.merge(games, how="cross")
    names["game"] = names.game.str.lower().replace("[^a-z0-9 ]", "").str.strip()

    match = names[names.game == names.game2].drop_duplicates().reset_index()
    print("games matching: " + ", ".join(match.game.unique().tolist()))

    leftovers = names[(~names.game.isin(match.game)) & (~names.game2.isin(match.game2))]
    if (leftovers.shape[0] > 0):
        leftovers["dist"] = leftovers.apply(lambda x: nltk.edit_distance(x.game, x.game2), axis=1)
        leftovers['r'] = leftovers.groupby('game2')['dist'].rank(method="first", ascending=False)
        match2 = leftovers[(leftovers['r'] == 1) & (leftovers.dist < 2)][['game', 'game2']]
        match = pd.concat([match, match2])

    print("games not matching: " + ", ".join(leftovers[~leftovers.game2.isin(match.game2)].game2.unique().tolist()))
    
    twitch.rename(columns = {"game": "game2"}, inplace=True)
    twitch = twitch.merge(match, on="game2", how="inner")
    twitch.drop(columns=['game2'], inplace=True)

    yt.rename(columns = {"game": "game2"}, inplace=True)
    yt = yt.merge(match, on="game2", how="inner")
    yt.drop(columns=['game2'], inplace=True)

    return twitch, yt


def fix_channel_names(twitch, yt, streamer_emails):
    names = pd.DataFrame({"channel": twitch.channel.unique().tolist() + yt.channel.unique().tolist()})
    names = names.merge(streamer_emails, on="channel", how="left")
    names = names[~names.email.isna()]

    names['n'] = names['channel'].str.len()
    names['r'] = names.groupby('email')['n'].rank(method="first", ascending=False)
    names = names[names['r'] == 1][['channel', 'email']]
    
    streamer_emails.rename(columns = {"channel": "ch"}, inplace=True)
    names = names.merge(streamer_emails, on="email", how="left")
    streamer_emails.rename(columns = {"ch": "channel"}, inplace=True)

    twitch.rename(columns = {"channel": "ch"}, inplace=True)
    twitch = twitch.merge(names[["channel", "ch"]], on="ch", how="left")
    twitch.channel.fillna(twitch.ch, inplace=True)
    twitch.drop(columns=['ch'], inplace=True)

    yt.rename(columns = {"channel": "ch"}, inplace=True)
    yt = yt.merge(names[["channel", "ch"]], on="ch", how="left")
    yt.channel.fillna(yt.ch, inplace=True)
    
    yt.drop(columns=['ch'], inplace=True)

    return twitch, yt


def merge_yt_twitch(twitch, youtube):
    streamer_emails = load_streamer_emails()

    twitch['channel'] = twitch['channel'].str.lower()
    youtube['channel'] = youtube['channel'].str.lower()
    
    # Set additional columns for twitch
    twitch['views'] = twitch['average_viewers']
    twitch['origin'] = 'twitch'
    twitch.drop('watch_time_hours', axis=1, inplace=True)  # Remove existing watch_time_hours
    twitch['watch_time_hours'] = twitch['stream_time_hours'] * twitch['views']

    twitch_channel = twitch.groupby(["channel"]).agg({"watch_time_hours":"sum"}).reset_index()
    twitch_channel.columns = ["channel", "watch_hours_twitch"]
    
    # Set column for youtube
    youtube['origin'] = 'youtube'
    
    print(f"yt: {youtube.watch_time_hours.sum()}; {youtube.watch_time_hours.mean()}")
    print(f"tw: {twitch.watch_time_hours.sum()}; {twitch.watch_time_hours.mean()}")
    twitch, youtube = fix_game_names(twitch, youtube)
    twitch, youtube = fix_channel_names(twitch, youtube, streamer_emails)

    yt_channel = youtube.groupby(["channel"]).agg({"watch_time_hours":"sum"}).reset_index()
    yt_channel.columns = ["channel", "watch_hours_yt"]

    # Combine files
    selected_cols = ['channel', 'game', 'watch_time_hours', 'stream_time_hours', 'views']
    full_dt = pd.concat([twitch[selected_cols], youtube[selected_cols]])

    # Aggregate at channel-game level
    channel_game = full_dt.groupby(['channel', 'game']).agg({
        'watch_time_hours': 'sum',
        'stream_time_hours': 'sum',
        'views': 'sum'
    }).reset_index()

    channel_game['rank_var'] = channel_game['watch_time_hours']
    channel_game['game_rank'] = channel_game.groupby('channel')['rank_var'].rank(ascending=False, method='dense')
    channel_game.sort_values('game_rank', inplace=True)

    rank1 = channel_game[channel_game.game_rank==1][["channel", "game", "watch_time_hours"]]
    rank1.columns = ["channel", "top_game", "top_game_watch_hours"]

    # Top streamer games
    top_games = channel_game.groupby('game').size().reset_index(name='N').sort_values(by='N', ascending=False)

    # Assuming channel_game DataFrame is already created and populated
    # Compute various sums and conditions
    channel = channel_game.groupby(['channel']).agg({
        'watch_time_hours': 'sum',
        'stream_time_hours': 'sum',
        'game': lambda x: ", ".join(x)
    }).reset_index()

    channel.columns = ['channel', 'watch_hours', 'stream_hours', 'games']
    channel["avg_viewers"] = channel.watch_hours / channel.stream_hours

    channel = channel.merge(yt_channel, on="channel", how = "left")
    channel = channel.merge(twitch_channel, on="channel", how = "left")
    
    channel["watch_hours_yt"].fillna(0, inplace=True)
    channel["pct_yt"] = channel["watch_hours_yt"] / channel["watch_hours"]
    channel.pct_yt.fillna(0, inplace=True)

    channel = channel.merge(rank1, on="channel", how="left")
    channel["pct_top_game"] = channel["top_game_watch_hours"] / channel["watch_hours"]
    channel.pct_top_game.fillna(1, inplace=True)

    channel = merge_streamer_emails(channel[['channel', 'avg_viewers', 'watch_hours', 'stream_hours', "pct_yt", "top_game", "pct_top_game", "games"]])
    return channel


def load_streamer_emails():
    # Load and clean streamer_emails data
    streamer_emails = pd.read_csv("streamer_emails.csv", header=0, encoding="latin1")
    streamer_emails['language'] = streamer_emails['language'].str.lower()
    streamer_emails['email'] = streamer_emails['email'].str.lower()
    streamer_emails = streamer_emails[streamer_emails['email'] != '']

    # Compute additional columns in streamer_emails
    streamer_emails['n'] = streamer_emails['language'].str.len() + 10 * streamer_emails['email'].str.contains('@')
    streamer_emails['r'] = streamer_emails.groupby('channel')['n'].rank(method="first", ascending=False)
    streamer_emails = streamer_emails[streamer_emails['r'] == 1][['channel', 'email', 'language']]
    return streamer_emails


def merge_streamer_emails(channel):
    streamer_emails = load_streamer_emails()
    # Merge with emails
    channel = pd.merge(channel, streamer_emails, on='channel', how='left')
    channel.email.fillna("", inplace=True)
    channel.language.fillna("", inplace=True)

    return channel
