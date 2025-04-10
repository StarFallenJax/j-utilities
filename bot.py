import discord
import json
import os
from discord.ext import commands

GIF_ROLE_FILE = "gif_roles.json"

def get_gif_roles_file_path():
    return os.path.abspath(GIF_ROLE_FILE)

print(f"[DEBUG] Path to gif_roles.json: {get_gif_roles_file_path()}")

def save_gif_roles():
    try:
        print(f"[DEBUG] Saving roles to {GIF_ROLE_FILE}...")
        with open(GIF_ROLE_FILE, "w", encoding="utf-8") as f:
            json.dump(gif_block_roles, f, indent=4)
            print(f"[DEBUG] Roles saved successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to save roles: {e}")

def load_gif_roles():
    try:
        if os.path.exists(GIF_ROLE_FILE):
            with open(GIF_ROLE_FILE, "r", encoding="utf-8") as f:
                roles = json.load(f)
                # Ensure guild ids are treated as strings (to match discord's format)
                print(f"[DEBUG] Successfully loaded roles: {roles}")
                return {str(guild_id): role_ids for guild_id, role_ids in roles.items()}
        else:
            print(f"[DEBUG] No existing file found. Initializing empty roles.")
            return {}
    except Exception as e:
        print(f"[ERROR] Error reading the JSON file: {e}")
        return {}

# Initialize gif_block_roles from the JSON file
gif_block_roles = load_gif_roles()

print(discord.__version__)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Bot Online')

@bot.command()
@commands.has_permissions(administrator=True)
async def setgifblockrole(ctx, *roles: discord.Role):
    """Sets the roles that will block GIFs for members with those roles."""
    if str(ctx.guild.id) not in gif_block_roles:
        gif_block_roles[str(ctx.guild.id)] = []

    for role in roles:
        if role.id not in gif_block_roles[str(ctx.guild.id)]:
            gif_block_roles[str(ctx.guild.id)].append(role.id)

    save_gif_roles()
    role_mentions = ', '.join([role.mention for role in roles])
    await ctx.send(f"✅ GIF block roles set to: {role_mentions}")

@bot.command()
@commands.has_permissions(administrator=True)
async def removegifblockrole(ctx, *roles: discord.Role):
    """Removes roles from the list that blocks GIFs."""
    if str(ctx.guild.id) in gif_block_roles:
        removed_roles = []
        for role in roles:
            if role.id in gif_block_roles[str(ctx.guild.id)]:
                gif_block_roles[str(ctx.guild.id)].remove(role.id)
                removed_roles.append(role)

        if removed_roles:
            save_gif_roles()
            removed_mentions = ', '.join([role.mention for role in removed_roles])
            await ctx.send(f"🧹 GIF block roles removed: {removed_mentions}")
        else:
            await ctx.send("⚠️ No such roles are currently blocking GIFs.")
    else:
        await ctx.send("⚠️ No GIF block roles are currently set.")

@bot.command()
async def showgifblockrole(ctx):
    """Shows the roles currently blocking GIFs."""
    if str(ctx.guild.id) in gif_block_roles and gif_block_roles[str(ctx.guild.id)]:
        roles = [ctx.guild.get_role(role_id) for role_id in gif_block_roles[str(ctx.guild.id)]]
        role_mentions = ', '.join([role.mention for role in roles if role])  # Mention all valid roles
        await ctx.send(f"🎯 Current blocked roles: {role_mentions}")
    else:
        await ctx.send("❌ No GIF-blocked roles set.")

# Show the help message
@bot.command(name="help")
async def help_command(ctx):
    help_text = (
        "**📘 Bot Commands:**\n\n"
        "**!setgifblockrole @Role** — Set a role whose messages containing GIFs will be auto-deleted.\n"
        "**!removegifblockrole @Role** — Remove the currently set GIF-blocked role.\n"
        "**!showgifblockrole** — Show the currently set GIF-blocked roles.\n"
        "**!help** — Show this help message.\n"
        "\n**Additional Information:**\n"
        "- **GIFs are automatically deleted** from members with the set role when sent as attachments, embeds, or links (e.g., Tenor).\n"
        "- The bot will log all deleted GIF messages to a channel named **mod-logs**.\n"
    )
    await ctx.send(help_text)

@bot.event
async def on_message(message):
    """Handles messages to check for GIFs from members with blocked roles."""
    if message.author.bot or not message.guild:
        return  # Ignore bots and DMs

    guild_id = str(message.guild.id)  # Ensure the guild_id is a string
    target_role_ids = gif_block_roles.get(guild_id, [])

    # Debugging role ids
    print(f"[DEBUG] Checking message from {message.author} in guild {message.guild.name}")
    print(f"[DEBUG] Blocked role ids for this guild: {target_role_ids}")

    # Check if the author has a GIF-blocking role
    has_blocked_role = any(role.id in target_role_ids for role in message.author.roles)
    print(f"[DEBUG] User {message.author} has a blocked role: {has_blocked_role}")

    if has_blocked_role:
        print(f"[DEBUG] User {message.author} has a blocked role. Checking for GIFs.")
        # Check for .gif in attachments
        for attachment in message.attachments:
            if attachment.content_type == "image/gif" or attachment.filename.endswith(".gif"):
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n{message.content}")
                print(f'[DEBUG] Deleted GIF attachment from {message.author}')
                return

        # Check for .gif in embeds
        for embed in message.embeds:
            if embed.image and embed.image.url and ".gif" in embed.image.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed image)")
                print(f'[DEBUG] Deleted GIF embed from {message.author}')
                return
            if embed.video and embed.video.url and ".gif" in embed.video.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed video)")
                print(f'[DEBUG] Deleted GIF video from {message.author}')
                return
            if embed.url and ".gif" in embed.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed URL)")
                print(f'[DEBUG] Deleted GIF link from {message.author}')
                return

        # Check for Tenor links
        if "https://tenor.com" in message.content.lower():
            await message.delete()
            log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
            if log_channel:
                await log_channel.send(f"🧹 Deleted Tenor link from {message.author.mention} in {message.channel.mention}:\n{message.content}")
            print(f'[DEBUG] Deleted Tenor link from {message.author}')
            return

    # Allow the bot to process other commands
    await bot.process_commands(message)

# Run the bot
bot.run('TOKEN')
