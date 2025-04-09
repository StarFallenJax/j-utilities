import discord
from discord.ext import commands

print(discord.__version__)

intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages
intents.guilds = True
intents.members = True  # Needed to check roles

bot = commands.Bot(command_prefix="?", intents=intents)

# Stores {guild_id: role_id} for which role to block GIFs for
gif_block_roles = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command to set the role that gets GIFs blocked
@bot.command()
@commands.has_permissions(administrator=True)
async def setgifblockrole(ctx, role: discord.Role):
    gif_block_roles[ctx.guild.id] = role.id
    await ctx.send(f"✅ GIF block role set to: {role.mention}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return  # Ignore bots and DMs

    guild_id = message.guild.id
    target_role_id = gif_block_roles.get(guild_id)

    if target_role_id and any(role.id == target_role_id for role in message.author.roles):
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
                print(f'Deleted a gif embed from {message.author}')
                return
            if embed.video and embed.video.url and ".gif" in embed.video.url:
                await message.delete()
                print(f'Deleted a gif video from {message.author}')
                return
            if embed.url and ".gif" in embed.url:
                await message.delete()
                print(f'Deleted a gif link from {message.author}')
                return

        # 3. Check for Tenor links in message content
        if "https://tenor.com" in message.content.lower():
            await message.delete()
            print(f'Deleted a Tenor link from {message.author}')
            return

    await bot.process_commands(message)  # Keep commands working

# Run the bot
bot.run('MTM1OTYwNzU5NDIzNDE1NTE5OQ.Gp8qkf.kRigwfvJUirmemXe48fKmP3mtVb5jJBjHg1EyE')
