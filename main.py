import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from aiohttp import web
import os
from dotenv import load_dotenv
import re
import random

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
COBALT_API_URL = os.getenv('COBALT_API_URL')

intents = discord.Intents.default()
intents.message_content = True

STATUS_LIST = [
    discord.CustomActivity(name="waiting for you to give me media links"),
    discord.CustomActivity(name="hotaro is rrly great, go check out his github [Hotaro26]"),
    discord.CustomActivity(name="playing wih urls"),
    discord.CustomActivity(name="the source code of mine is available on hotaro's github!"),
    discord.CustomActivity(name="pls interact with me im so lonely")
]

class GabiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sync the slash commands to Discord
        await self.tree.sync()
        # Start dummy web server for hosting
        self.loop.create_task(self.web_server())
        # Start the status shuffle loop
        self.status_task.start()

    async def web_server(self):
        app = web.Application()
        app.router.add_get('/', lambda request: web.Response(text="Gabi is running!"))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 7860)
        await site.start()
        print("✅ Dummy web server started on port 7860")

    @tasks.loop(minutes=5)
    async def status_task(self):
        # Pick a random status from the list and apply it
        await self.change_presence(activity=random.choice(STATUS_LIST))

    @status_task.before_loop
    async def before_status_task(self):
        # Make sure the bot is fully ready before trying to set the status
        await self.wait_until_ready()


bot = GabiBot()
URL_REGEX = r'(https?://[^\s]+)'

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.tree.command(name="about", description="Learn about Gabi and her creator!")
async def about(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌸 About Gabi",
        description="I am an all-in-one media downloader bot! Just paste a link and I'll do the rest.",
        color=discord.Color.pink()
    )
    embed.add_field(name="Author", value="Aki (Hotaro26)")
    embed.add_field(name="GitHub", value="[gabi_discord_bot](https://github.com/Hotaro26/gabi_discord_bot)")
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
        
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="💻 Hotaro's GitHub", url="https://github.com/Hotaro26", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="🤖 Bot Code", url="https://github.com/Hotaro26/gabi_discord_bot", style=discord.ButtonStyle.link))
        
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="supports", description="See which platforms Gabi can download from")
async def supports(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ Supported Platforms",
        description=(
            "I can download media from almost anywhere! Some of the main platforms include:\n\n"
            "▶️ **YouTube** (Videos, Shorts, Music)\n"
            "🎵 **TikTok** (Videos, Photos, Audio)\n"
            "📸 **Instagram** (Reels, Posts, Stories)\n"
            "📌 **Pinterest** (Videos & Images)\n"
            "🐦 **X / Twitter** (Videos & Voice)\n"
            "💬 **Reddit** (Videos & Audio)\n"
            "👻 **Snapchat** (Spotlights)\n\n"
            "...and many more!"
        ),
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Clear a specific number of messages from the chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    # Acknowledge the interaction privately first since purging takes time
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Successfully cleared {len(deleted)} messages!", ephemeral=True)

@clear.error
async def clear_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You need 'Manage Messages' permissions to use this!", ephemeral=True)

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
                                
                                # Create a clickable UI Button
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="📥 Download", url=stream_url, style=discord.ButtonStyle.link))
                                
                                # Send the raw URL + buttons (No custom embed, otherwise Discord hides the video player!)
                                await message.reply(content=stream_url, view=view)
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
    else:
        bot.run(TOKEN)
