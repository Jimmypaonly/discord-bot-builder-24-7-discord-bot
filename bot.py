# bot.py - Complete file for Render deployment
from flask import Flask, render_template_string, jsonify
import discord
from discord.ext import commands
import asyncio
import threading
import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='', intents=intents)
bot_running = False
bot_thread = None

def is_admin(member: discord.Member) -> bool:
    """Check if member has admin or manage channels permissions"""
    return (member.guild_permissions.administrator or 
            member.guild_permissions.manage_channels)

@bot.event
async def on_ready():
    global bot_running
    bot_running = True
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    logger.info(f"Discord bot ready - Tag: {bot.user.tag}, Client ID: {bot.user.id}")
    logger.info(f"Invite URL: {invite_url}")
    print(f"\n✅ Bot is online as {bot.user}")
    print(f"📎 Invite URL: {invite_url}\n")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if not message.guild or not message.member:
        return
    
    if not is_admin(message.member):
        return
    
    # Only respond when the bot is mentioned
    if not bot.user.mentioned_in(message):
        return
    
    # Strip the bot mention from the message to get the command
    content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip().lower()
    guild = message.guild
    
    try:
        # Make all channels private
        if content == "make all channels private":
            channels = []
            for channel in guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    channels.append(channel)
            
            count = 0
            for channel in channels:
                await channel.set_permissions(guild.default_role, view_channel=False)
                count += 1
            
            await message.reply(f"Done! Made **{count} channels** private. @everyone can no longer see them.")
            return
        
        # Show #channel to everyone
        show_match = re.match(r'^show\s+<#(\d+)>\s+to\s+everyone$', content)
        if show_match:
            channel_id = int(show_match.group(1))
            target = guild.get_channel(channel_id)
            if not target:
                await message.reply("I couldn't find that channel.")
                return
            
            await target.set_permissions(guild.default_role, view_channel=True)
            await message.reply(f"Done! <#{channel_id}> is now visible to everyone.")
            return
        
        # Give [role] all channels
        give_all_match = re.match(r'^give\s+<@&(\d+)>\s+all\s+channels$', content)
        if give_all_match:
            role_id = int(give_all_match.group(1))
            role = guild.get_role(role_id)
            if not role:
                await message.reply("I couldn't find that role.")
                return
            
            channels = []
            for channel in guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    channels.append(channel)
            
            count = 0
            for channel in channels:
                await channel.set_permissions(role, view_channel=True)
                count += 1
            
            await message.reply(f"Done! **{role.name}** can now see all **{count} channels**.")
            return
        
        # Give [role] #channel
        give_one_match = re.match(r'^give\s+<@&(\d+)>\s+<#(\d+)>$', content)
        if give_one_match:
            role_id = int(give_one_match.group(1))
            channel_id = int(give_one_match.group(2))
            role = guild.get_role(role_id)
            target = guild.get_channel(channel_id)
            
            if not role:
                await message.reply("I couldn't find that role.")
                return
            if not target:
                await message.reply("I couldn't find that channel.")
                return
            
            await target.set_permissions(role, view_channel=True)
            await message.reply(f"Done! **{role.name}** can now see <#{channel_id}>.")
            return
        
        # Help command
        if content == "help":
            help_text = (
                "**Ping me + one of these commands:**\n\n"
                "• `@Bot make all channels private` — hide all channels from @everyone\n"
                "• `@Bot give @Role all channels` — let a role see every channel\n"
                "• `@Bot give @Role #channel` — let a role see one specific channel\n"
                "• `@Bot show #channel to everyone` — make a channel visible to everyone again"
            )
            await message.reply(help_text)
    
    except Exception as err:
        logger.error(f"Error handling message: {err}")
        try:
            await message.reply("Something went wrong. Make sure I have Administrator permissions.")
        except:
            pass

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Discord client error in {event}")

@app.route('/')
def index():
    """Home page showing bot status"""
    status = "🟢 Running" if bot_running else "🔴 Stopped"
    status_color = "green" if bot_running else "red"
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Manager</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 30px;
                max-width: 600px;
                margin: 0 auto;
                backdrop-filter: blur(10px);
            }
            .status {
                font-size: 24px;
                margin: 20px 0;
                padding: 15px;
                border-radius: 10px;
                background: rgba(0, 0, 0, 0.2);
            }
            .status-dot {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
            }
            .green { background-color: #4CAF50; box-shadow: 0 0 10px #4CAF50; }
            .red { background-color: #f44336; box-shadow: 0 0 10px #f44336; }
            .commands {
                text-align: left;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
                padding: 20px;
                margin-top: 20px;
            }
            .commands h3 {
                margin-top: 0;
            }
            .command {
                font-family: monospace;
                background: rgba(0, 0, 0, 0.3);
                padding: 5px 10px;
                border-radius: 5px;
                margin: 5px 0;
                display: inline-block;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
                font-size: 16px;
            }
            button:hover {
                background: #45a049;
            }
            .footer {
                margin-top: 30px;
                font-size: 12px;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot Manager</h1>
            <div class="status">
                <span class="status-dot {{ status_color }}"></span>
                Bot Status: {{ status }}
            </div>
            <div class="commands">
                <h3>📝 Available Commands (mention the bot):</h3>
                <div class="command">@Bot make all channels private</div><br>
                <div class="command">@Bot give @Role all channels</div><br>
                <div class="command">@Bot give @Role #channel</div><br>
                <div class="command">@Bot show #channel to everyone</div><br>
                <div class="command">@Bot help</div>
            </div>
            <button onclick="location.reload()">🔄 Refresh Status</button>
            <div class="footer">
                <small>Bot needs Administrator permissions to work properly</small>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html, status=status, status_color=status_color)

@app.route('/status')
def status():
    """API endpoint to check bot status"""
    return jsonify({
        'running': bot_running,
        'status': 'running' if bot_running else 'stopped'
    })

def run_bot():
    """Run the Discord bot"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.warning("DISCORD_BOT_TOKEN not set — bot will not start")
        print("❌ ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set it in Render Dashboard under Environment Variables")
        return
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to log in to Discord: {e}")
        print(f"❌ Failed to start bot: {e}")

def start_bot_thread():
    """Start the Discord bot in a separate thread"""
    global bot_thread
    if not bot_thread or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started")
        print("🚀 Bot thread started successfully")

if __name__ == '__main__':
    # Get token from environment variable
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("=" * 50)
        print("⚠️  WARNING: DISCORD_BOT_TOKEN environment variable not set")
        print("Please set it in Render Dashboard:")
        print("  - Go to your service → Environment → Add Environment Variable")
        print("  - Key: DISCORD_BOT_TOKEN")
        print("  - Value: your_discord_bot_token_here")
        print("=" * 50)
    else:
        print("=" * 50)
        print("✅ DISCORD_BOT_TOKEN found!")
    
    # Start the Discord bot in a background thread
    start_bot_thread()
    
    # Run Flask server
    port = int(os.getenv('PORT', 5000))
    print(f"\n🌐 Flask server starting on port {port}")
    print(f"📊 Web dashboard available at: http://localhost:{port}")
    print("=" * 50)
    print("\n🚀 Bot is starting... Press Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
