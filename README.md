# Gabi Discord Bot

Hey! This is a simple Discord bot I made that automatically extracts direct video/media links from social media URLs. Just drop a link (like YouTube, TikTok, Pinterest, etc.) in the chat, and Gabi will instantly reply with the direct file stream!

## How it works
It listens for any messages containing a URL and passes them to my self-hosted Cobalt API backend.

## Hosting it yourself
If you want to run this yourself:
1. Make sure you have your own Cobalt API instance running.
2. Put your Discord bot token and Cobalt URL into an Environment Variable or `.env` file.
3. Run `python main.py`!
