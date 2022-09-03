# tacocat

## Description

**tacocat** is my multipurpose Discord bot project. It is the successor of my previous discontinued project, TacoBot. This rewrite is motivated by a clearer vision and intention to adhere to cleaner coding practices. I hope to expand this project to a scale impressive enough to include in a coding portfolio.

This time around, I will be using Discord's new command feature, [slash commands](https://discord.com/blog/slash-commands-are-here), in addition to traditional prefixed commands. I will continue to use [Rapptz's discord.py API wrapper](https://github.com/Rapptz/discord.py) since v2.0 has been officially distributed on PyPI, and it provides support for slash commands and UI components.

## Intended Features

- Streaming music from a variety of platforms, such as YouTube, Spotify, and SoundCloud.
- Maintain, save, and load playlists that can mix and match tracks or playlists from any of these platforms.
- Perform basic moderation duties, such as managing roles, users, purging spam, etc.
- Miscellaneous convenience features, like currency and timezone conversion, math tools, Python within Discord, etc.
- Basically any little feature that makes me think, "but what if I could do all that without leaving the Discord app?" In that sense, I hope this bot can be an always ongoing passion project where I continually find something to add.

## Recovery Instructions

In the event of an emergency, for the program to work after cloning the repository:

1. Create and fill a [`.env`](#environment-variables) file at the project root.
2. Initialize a virtual environment and [install dependencies](#virtual-environment).
3. Run the program like you normally have with either:

```
python -m bot  # Execute package
./run          # PS script that does the same thing
```

### Environment Variables

When running locally on my machine, contents of the `.env` file are exposed in the [bot package](bot/) with [python-dotenv](https://pypi.org/project/python-dotenv/). As of now, the required environment variables are:

- BOT_TOKEN - can be regenerated on [Discord developer portal](https://discord.com/developers/applications).
- BOT_VERSION - version string.
- BOT_MODE - `production` if deployed, anything else otherwise.
- DEBUG_VERBOSE - `False` to disable debugging verbosity, anything else otherwise.
- TEST_GUILD_ID - ID of Discord testing server.
- DEVELOPER_USER_ID - my Discord user ID, be sure to activate "Developer Mode" in Discord app.
- SUPERUSER_USER_IDS - comma-separated (`MIND_THE, SPACE_THERE`) Discord IDs of users that I grant superuser privilege to.
- SPOTIFY_CLIENT_ID - client ID for Spotify app, can be found on [Spotify developer dashboard](https://developer.spotify.com/dashboard/applications).
- SPOTIFY_CLIENT_SECRET - client secret for Spotify app, can be found on [Spotify developer dashboard](https://developer.spotify.com/dashboard/applications).

### Virtual Environment

The state of the virtual environment used during development is maintained in [requirements.txt](requirements.txt). You can recreate it like you normally would; at the project root, run:
```
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```
