import discord
print(discord.__version__)
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages
intents.guilds = True
intents.members = True  # Needed to check roles

bot = commands.Bot(command_prefix="!", intents=intents)

# Change this to the exact name of the role you want to target
TARGET_ROLE_ID = 1359611917320192190

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
 # 1359611917320192190
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore other bots
    
    if message.guild:
        if any(role.id == TARGET_ROLE_ID for role in message.author.roles):
            # 1. Check for .gif in attachments
            for attachment in message.attachments:
                if attachment.content_type == "image/gif" or attachment.filename.endswith(".gif"):
                    await message.delete()
                    print(f'Deleted a gif message from {message.author}')
                    return

            # 2. Check for .gif in embeds
            for embed in message.embeds:
                if embed.image and embed.image.url and ".gif" in embed.image.url:
                    await message.delete()
                    return
                if embed.video and embed.video.url and ".gif" in embed.video.url:
                    await message.delete()
                    return
                if embed.url and ".gif" in embed.url:
                    await message.delete()
                    return

            # 3. Check for Tenor links in message content
            if "https://tenor.com" in message.content.lower():
                await message.delete()
                print(f'Deleted a gif message from {message.author}')
                return

    await bot.process_commands(message)  # Keep other commands working

# Run the bot
bot.run('MTM1OTYwNzU5NDIzNDE1NTE5OQ.Gp8qkf.kRigwfvJUirmemXe48fKmP3mtVb5jJBjHg1EyE')
