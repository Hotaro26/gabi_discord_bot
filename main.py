import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# E.g. https://your-space-name.hf.space/
COBALT_API_URL = os.getenv('COBALT_API_URL')

# Intents are required to read message content
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Basic regex to find URLs in a message
URL_REGEX = r'(https?://[^\s]+)'

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    # Ignore messages sent by bots (including ourselves)
    if message.author.bot:
        return

    # Look for a URL in the user's message
    match = re.search(URL_REGEX, message.content)
    if match:
        url = match.group(0)
        
        # Show the bot is "typing..." while it waits for the Cobalt API
        async with message.channel.typing():
            try:
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                payload = {
                    "url": url
                }
                
                async with aiohttp.ClientSession() as session:
                    # Make a POST request to your Cobalt API
                    async with session.post(COBALT_API_URL, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            # Cobalt typically returns status: 'redirect', 'stream', 'picker' or 'error'
                            if data.get('status') in ['redirect', 'stream']:
                                stream_url = data.get('url')
                                await message.reply(f"Here is your direct stream link: {stream_url}")
                            else:
                                print(f"Cobalt response: {data}")
                        else:
                            print(f"Error: Received HTTP {resp.status} from Cobalt API")
                            
            except Exception as e:
                print(f"Error processing link: {e}")

    # Ensure other commands still work
    await bot.process_commands(message)

if __name__ == '__main__':
    if not TOKEN or TOKEN == 'your_discord_bot_token_here':
        print("❌ Error: Please set a valid DISCORD_TOKEN in the .env file")
    elif not COBALT_API_URL or COBALT_API_URL == 'https://your-huggingface-space.hf.space':
        print("❌ Error: Please set your COBALT_API_URL in the .env file")
    else:
        bot.run(TOKEN)
