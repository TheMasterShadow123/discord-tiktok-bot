import discord
import os
import sys
import yt_dlp
import asyncio
import subprocess
import time
from typing import Literal
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
        print("✅ Slash commands synced!")

bot = TiktokBot()

async def convert_to_h264(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-profile:v', 'main',
        '-level', '4.2',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        output_path
    ]

    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()
    
    if process.returncode != 0:
        print(f"❌ Transcode failed with code {process.returncode}")
        return False
    return True

async def emergency_compress(input_path, output_path, target_size_mb):
    probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path]
    try:
        duration = float(subprocess.check_output(probe_cmd).decode().strip())
    except:
        return False

    target_bitrate = (target_size_mb * 0.9 * 8192 * 1000) / duration

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', "scale='min(1280,iw)':-2,fps=30",
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-b:v', str(int(target_bitrate)),
        '-maxrate', str(int(target_bitrate * 1.5)),
        '-bufsize', str(int(target_bitrate * 2)),
        '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()
    return os.path.exists(output_path)

@bot.tree.command(name="tiktok", description="Download a TikTok video")
@app_commands.describe(
    url="Paste the TikTok link here", 
    mode="Auto: Optimizes for Discord. Full: Raw upload (May fail if >10MB)"
)
async def tiktok(
    interaction: discord.Interaction, 
    url: str, 
    mode: Literal['Auto (Smart)', 'Full (Raw)'] = 'Auto (Smart)'
):
    await interaction.response.defer(thinking=True)
    
    async def update_status(text):
        try:
            await interaction.edit_original_response(content=text)
        except:
            pass

    await update_status("⬇️ Downloading... (Fetching from TikTok)")
    print(f"⬇️ Downloading: {url}")
    
    timestamp = int(time.time())
    
    ydl_opts = {
        'outtmpl': f'temp_{timestamp}_%(id)s.%(ext)s',
        'cookiefile': COOKIES_FILE,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False, 
        'format': 'best', 
    }

    raw_filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_filename = ydl.prepare_filename(info)
            if not os.path.exists(raw_filename):
                 base, _ = os.path.splitext(raw_filename)
                 for ext in ['.mp4', '.mkv', '.webm']:
                     if os.path.exists(base + ext): raw_filename = base + ext; break
    except Exception as e:
        await interaction.followup.send(f"❌ Download failed: {e}")
        return

    final_file = None

    if raw_filename and os.path.exists(raw_filename):
        if mode == 'Full (Raw)':
            await update_status("📦 Preparing Raw Upload... (Skipping conversion)")
            final_file = raw_filename

        else:
            hq_filename = f"hq_{timestamp}.mp4"
            
            await update_status("🎬 Transcoding... (Fixing for Windows/Discord)")
            success = await convert_to_h264(raw_filename, hq_filename)
            
            if success and os.path.exists(hq_filename):
                size_mb = os.path.getsize(hq_filename) / (1024 * 1024)
                
                if size_mb > MAX_SIZE_MB:
                    await update_status(f"📉 Compressing... ({size_mb:.1f}MB -> 10MB)")
                    compressed_filename = f"small_{timestamp}.mp4"
                    await emergency_compress(hq_filename, compressed_filename, MAX_SIZE_MB)
                    
                    final_file = compressed_filename
                    if os.path.exists(hq_filename): os.remove(hq_filename)
                else:
                    final_file = hq_filename
            else:
                await interaction.followup.send("❌ Processing failed.")
                return

        if final_file and os.path.exists(final_file):
            await update_status("🚀 Uploading to Discord...")
            print(f"🚀 Uploading: {final_file}")
            try:
                await interaction.followup.send(
                    content="", 
                    file=discord.File(final_file, filename="1.mp4")
                )
                await interaction.delete_original_response()
                
            except Exception as e:
                print(f"❌ Upload Error: {e}")
                await interaction.followup.send(f"❌ Upload Failed: {e}")
            finally:
                if os.path.exists(final_file): os.remove(final_file)
        
        if os.path.exists(raw_filename): os.remove(raw_filename)
    else:
        await interaction.followup.send("❌ Error: File not found after download.")

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN missing in .env")
