import discord
import json
import os
from discord.ext import commands

GIF_ROLE_FILE = "gif_roles.json"

# Load existing data
if os.path.exists(GIF_ROLE_FILE):
    with open(GIF_ROLE_FILE, "r") as f:
        gif_block_roles = json.load(f)
        # Ensure each guild has a list (even if empty)
        for guild_id in gif_block_roles:
            if not isinstance(gif_block_roles[guild_id], list):
                gif_block_roles[guild_id] = []
else:
    gif_block_roles = {}

# Define the function to save gif roles to the JSON file
def save_gif_roles():
    with open(GIF_ROLE_FILE, "w") as f:
        json.dump(gif_block_roles, f, indent=4)

print(discord.__version__)

intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages
intents.guilds = True
intents.members = True  # Needed to check roles

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)


# Command to set the role that gets GIFs blocked
@bot.command()
@commands.has_permissions(administrator=True)
async def setgifblockrole(ctx, *roles: discord.Role):
    if ctx.guild.id not in gif_block_roles:
        gif_block_roles[ctx.guild.id] = []

    for role in roles:
        if role.id not in gif_block_roles[ctx.guild.id]:
            gif_block_roles[ctx.guild.id].append(role.id)
    
    save_gif_roles()
    role_mentions = ', '.join([role.mention for role in roles])
    await ctx.send(f"✅ GIF block roles set to: {role_mentions}")

# Command to remove the GIF block role
@bot.command()
@commands.has_permissions(administrator=True)
async def removegifblockrole(ctx, *roles: discord.Role):
    if ctx.guild.id in gif_block_roles:
        removed_roles = []
        for role in roles:
            if role.id in gif_block_roles[ctx.guild.id]:
                gif_block_roles[ctx.guild.id].remove(role.id)
                removed_roles.append(role)
        
        if removed_roles:
            save_gif_roles()
            removed_mentions = ', '.join([role.mention for role in removed_roles])
            await ctx.send(f"🧹 GIF block roles removed: {removed_mentions}")
        else:
            await ctx.send("⚠️ No such roles are currently blocking GIFs.")
    else:
        await ctx.send("⚠️ No GIF block roles are currently set.")

# Command to show the current GIF block roles
@bot.command()
async def showgifblockrole(ctx):
    if ctx.guild.id in gif_block_roles and gif_block_roles[ctx.guild.id]:
        roles = [ctx.guild.get_role(role_id) for role_id in gif_block_roles[ctx.guild.id]]
        role_mentions = ', '.join([role.mention for role in roles if role])  # Mention all valid roles
        await ctx.send(f"🎯 Current blocked roles: {role_mentions}")
    else:
        await ctx.send("❌ No GIF-blocked roles set.")

# Show the help message
@bot.command(name="help")
async def help_command(ctx):
    help_text = (
        "**📘 Bot Commands:**\n\n"
        "**?setgifblockrole @Role** — Set a role whose messages containing GIFs will be auto-deleted.\n"
        "**?removegifblockrole** — Remove the currently set GIF-blocked role.\n"
        "**?showgifblockrole** — Show the currently set GIF-blocked role.\n"
        "**?help** — Show this help message.\n"
        "\n**Additional Information:**\n"
        "- **GIFs are automatically deleted** from members with the set role when sent as attachments, embeds, or links (e.g., Tenor).\n"
        "- The bot will log all deleted GIF messages to a channel named **mod-logs**.\n"
    )
    await ctx.send(help_text)


# Inside your message deletion logic
log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
if log_channel:
    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n{message.content}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return  # Ignore bots and DMs

    guild_id = message.guild.id
    target_role_ids = gif_block_roles.get(guild_id, [])

    if any(role.id in target_role_ids for role in message.author.roles):
        # Check for .gif in attachments
        for attachment in message.attachments:
            if attachment.content_type == "image/gif" or attachment.filename.endswith(".gif"):
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n{message.content}")
                print(f'Deleted a gif message from {message.author}')
                return

        # Check for .gif in embeds
        for embed in message.embeds:
            if embed.image and embed.image.url and ".gif" in embed.image.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed)")
                print(f'Deleted a gif embed from {message.author}')
                return
            if embed.video and embed.video.url and ".gif" in embed.video.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed video)")
                print(f'Deleted a gif video from {message.author}')
                return
            if embed.url and ".gif" in embed.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed url)")
                print(f'Deleted a gif link from {message.author}')
                return

        # Check for Tenor links
        if "https://tenor.com" in message.content.lower():
            await message.delete()
            log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
            if log_channel:
                await log_channel.send(f"🧹 Deleted Tenor link from {message.author.mention} in {message.channel.mention}:\n{message.content}")
            print(f'Deleted a Tenor link from {message.author}')
            return

    await bot.process_commands(message)

# Run the bot
bot.run('MTM1OTYwNzU5NDIzNDE1NTE5OQ.Gp8qkf.kRigwfvJUirmemXe48fKmP3mtVb5jJBjHg1EyE')
