import discord
import os
import sys
import yt_dlp
import asyncio
import subprocess
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "darwin":
    os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"

TOKEN = os.getenv('DISCORD_TOKEN')
COOKIES_FILE = 'cookies.txt'
MAX_SIZE_MB = 10

class TiktokBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Synced slash commands!")

bot = TiktokBot()

async def compress_video(input_path, output_path, target_size_mb):
    probe_cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', input_path
    ]
    try:
        duration = float(subprocess.check_output(probe_cmd).decode().strip())
    except Exception as e:
        print(f"❌ FFprobe failed: {e}")
        return False

    target_total_bitrate = (target_size_mb * 0.90 * 8192 * 1000) / duration
    audio_bitrate = 128 * 1000
    video_bitrate = target_total_bitrate - audio_bitrate

    if video_bitrate < 100000:
        video_bitrate = 100000

    vf_filter = "scale='min(720,iw)':-2,fps=30,format=yuv420p"

    print(f"ℹ️ Compressing to 720p/30fps @ {int(video_bitrate/1000)}kbit/s")

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', vf_filter,
        '-af', 'aresample=async=1',
        '-c:v', 'libx264',
        '-b:v', str(int(video_bitrate)),
        '-maxrate', str(int(video_bitrate * 1.5)),
        '-bufsize', str(int(video_bitrate * 2)),
        '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '128k',
        output_path
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"❌ FFmpeg Error:\n{stderr.decode()}")
        return False

    return os.path.exists(output_path)

@bot.tree.command(name="tiktok", description="Download a TikTok video")
@app_commands.describe(url="Paste the TikTok link here")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def tiktok(interaction: discord.Interaction, url: str):
    if "tiktok.com" not in url:
        await interaction.response.send_message("❌ That doesn't look like a valid TikTok link.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s-%(id)s.%(ext)s',
        'cookiefile': COOKIES_FILE,
        'noplaylist': True,
        'quiet': True,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-k', '1M'],
    }

    filename = None

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                break
        except Exception as e:
            error_msg = str(e)
            if "Unable to extract webpage" in error_msg or "403" in error_msg:
                print(f"⚠️ Attempt {attempt+1} failed. Retrying...")
                await asyncio.sleep(2)
                if attempt == max_retries - 1:
                    await interaction.followup.send("❌ TikTok blocked the download (Try again later).")
                    return
            else:
                await interaction.followup.send(f"❌ Download failed: {error_msg}")
                return

    if filename and os.path.exists(filename):
        try:
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            if file_size_mb > MAX_SIZE_MB:
                await interaction.followup.send(f"⚠️ Video is {file_size_mb:.1f}MB. Optimizing...", ephemeral=True)

                compressed_filename = f"compressed_{filename}"
                success = await compress_video(filename, compressed_filename, MAX_SIZE_MB)

                if success:
                    os.remove(filename)
                    filename = compressed_filename
                else:
                    await interaction.followup.send("❌ Compression failed (Check logs). Uploading original...", ephemeral=True)

            await interaction.followup.send(file=discord.File(filename))

        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Upload Failed: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found. Did you create the .env file?")
else:
    bot.run(TOKEN)
