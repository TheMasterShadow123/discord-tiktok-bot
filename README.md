# Discord TikTok Downloader

A high-performance Discord bot that downloads TikToks, fixes audio sync issues, and compresses videos to fit Discord’s 10MB upload limit while preserving smooth 60fps playback.

### FEATURES

- Smart Compression – Automatically shrinks videos to under 10MB
- 60fps Support – Maintains smooth motion
- Lag & Sync Fix – Uses aria2 for fast downloads and ffmpeg to fix audio drift
- Cross-Platform – Works on Windows, macOS, and Linux

### INSTALLATION GUIDE

#### 1. PREREQUISITES

- Python 3.9+
  <https://www.python.org/downloads/>

- Git
  <https://git-scm.com/downloads/>

- Discord Bot Token
  <https://discord.com/developers/applications>

### 2. INSTALL SYSTEM TOOLS

The bot requires FFmpeg and Aria2.

**WINDOWS**

Open PowerShell as Administrator and run:

    winget install Gyan.FFmpeg
    winget install aria2

Restart your terminal after installing.

**MACOS**

Requires Homebrew:

    brew install ffmpeg aria2

**LINUX (Ubuntu / Debian)**

    sudo apt update && sudo apt install ffmpeg aria2 -y

### 3. PROJECT SETUP

Clone the Repository:

    git clone https://github.com/TheMasterShadow123/discord-tiktok-bot.git
    cd discord-tiktok-bot

Install Python Dependencies:

    pip install -r requirements.txt

If that fails on Windows:

    python -m pip install -r requirements.txt

### 4. SECURITY CONFIGURATION (IMPORTANT)

Create a .env file to store your Discord bot token.
This file is ignored by Git.

- Create a file called .env

- Add your token to the file:

    DISCORD_TOKEN=paste_your_discord_bot_token_here

### OPTIONAL: TIKTOK COOKIE SETUP

If TikTok blocks downloads:

1. Install a browser extension such as "Get cookies.txt"
2. Head to the TikTok website (Make sure you are logged in)
3. Export your TikTok cookies
4. Save the file as cookies.txt
5. Place it in the project root directory

### 5. RUN THE BOT

**Mac / Linux:**

    python main.py

**Windows:**

    python main.py

If successful, you will see:

    Logged in as [YourBotName]

NOTES

- FFmpeg and Aria2 must be available in PATH
- Discord upload limit is 10MB for non-Nitro servers
- Cookies are optional but improve reliability
