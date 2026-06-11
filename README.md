# GameLink Discord Bot

GameLink is a Discord bot that allows you to connect multiple game platforms (Roblox, Xbox) to your Discord account for verification and role assignment.

## Features
- **/setup**: Configure the bot for your server.
- **Verification**: Roblox (Bio Emoji method) and Xbox (Discord Connections method).
- **Lookups**: Cross-reference Discord and game accounts.
- **Persistent UI**: Use `/verifybutton` to post a permanent verification embed.

## Hosting on Railway
1. Push this code to a GitHub repository.
2. Link the repository to Railway.
3. Railway will automatically detect the `requirements.txt` and `Procfile` to run the bot.

## Configuration
The bot token and client details are stored in `config.py`. For production, it is recommended to use environment variables.
