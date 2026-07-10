import discord
from discord.ext import commands
import aiohttp
from aiohttp import web
import os
from dotenv import load_dotenv
import re

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
COBALT_API_URL = os.getenv('COBALT_API_URL')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

URL_REGEX = r'(https?://[^\s]+)'

# --- Dummy Web Server to keep Hugging Face awake ---
async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Gabi is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 7860) # HF uses port 7860
    await site.start()
    print("✅ Dummy web server started on port 7860")

@bot.event
async def setup_hook():
    bot.loop.create_task(web_server())

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    match = re.search(URL_REGEX, message.content)
    if match:
        url = match.group(0)
        
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
                    async with session.post(COBALT_API_URL, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            if data.get('status') in ['redirect', 'stream']:
                                stream_url = data.get('url')
                                await message.reply(f"Here is your direct stream link: {stream_url}")
                            else:
                                print(f"Cobalt response: {data}")
                        else:
                            print(f"Error: Received HTTP {resp.status} from Cobalt API")
                            
            except Exception as e:
                print(f"Error processing link: {e}")

    await bot.process_commands(message)

if __name__ == '__main__':
    if not TOKEN or TOKEN == 'your_discord_bot_token_here':
        print("❌ Error: Please set a valid DISCORD_TOKEN in the .env file")
    elif not COBALT_API_URL or COBALT_API_URL == 'https://your-huggingface-space.hf.space':
        print("❌ Error: Please set your COBALT_API_URL in the .env file")
    else:
        bot.run(TOKEN)
