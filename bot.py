import discord
import json
import os
import asyncio
from discord.ext import commands
import sqlite3
import atexit

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('starboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS starboard_messages (
            original_msg_id INTEGER PRIMARY KEY,
            starboard_msg_id INTEGER,
            guild_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Run at startup
init_db()

# Create connection pool
def get_db():
    conn = sqlite3.connect('starboard.db')
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

# Close all connections on exit
@atexit.register
def close_db():
    if 'db' in globals():
        globals()['db'].close()

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


STARBOARD_FILE = "starboards.json"

def get_starboard_file_path():
    return os.path.abspath(STARBOARD_FILE)

def load_starboards():
    try:
        if os.path.exists(STARBOARD_FILE):
            with open(STARBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded starboard config: {data}")
                return data
    except Exception as e:
        print(f"[ERROR] Failed to load starboards: {e}")
    return {}

def save_starboards():
    try:
        with open(STARBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(starboards, f, indent=4)
        print("[DEBUG] Starboard config saved.")
    except Exception as e:
        print(f"[ERROR] Failed to save starboards: {e}")

starboards = load_starboards()


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
async def starboard(ctx, board_name: str, subcommand: str, *args):
    guild_id = str(ctx.guild.id)
    if guild_id not in starboards:
        starboards[guild_id] = {}

    if subcommand == "create":
        if board_name not in starboards[guild_id]:
            starboards[guild_id][board_name] = {}
            save_starboards()
            await ctx.send(f"✅ Starboard '{board_name}' created.")
        else:
            await ctx.send("⚠️ That starboard already exists.")

    elif subcommand == "delete":
        if board_name in starboards[guild_id]:
            del starboards[guild_id][board_name]
            save_starboards()
            await ctx.send(f"🗑️ Deleted starboard '{board_name}'.")
        else:
            await ctx.send("❌ Starboard does not exist.")

    elif subcommand == "add":
        if board_name not in starboards[guild_id]:
            await ctx.send("❌ Starboard not found.")
            return
        if args[0] == "reaction" and len(args) == 3:
            emoji, threshold = args[1], int(args[2])
            starboards[guild_id][board_name][emoji] = starboards[guild_id][board_name].get(emoji, {})
            starboards[guild_id][board_name][emoji]["threshold"] = threshold
            save_starboards()
            await ctx.send(f"⭐ Reaction '{emoji}' set with threshold {threshold} for starboard '{board_name}'.")
        elif args[0] == "channel" and len(args) == 2:
            channel = discord.utils.get(ctx.guild.text_channels, name=args[1]) or ctx.guild.get_channel(int(args[1]))
            if not channel:
                await ctx.send("❌ Channel not found.")
                return
            for emoji in starboards[guild_id][board_name]:
                starboards[guild_id][board_name][emoji]["channel_id"] = channel.id
            save_starboards()
            await ctx.send(f"📌 Channel set to {channel.mention} for starboard '{board_name}'.")

    elif subcommand == "remove":
        if board_name not in starboards[guild_id]:
            await ctx.send("❌ Starboard not found.")
            return
        if args[0] == "reaction" and len(args) == 2:
            emoji = args[1]
            if emoji in starboards[guild_id][board_name]:
                del starboards[guild_id][board_name][emoji]
                save_starboards()
                await ctx.send(f"🧹 Removed emoji '{emoji}' from starboard '{board_name}'.")
            else:
                await ctx.send("⚠️ Emoji not found in that starboard.")
        elif args[0] == "channel":
            for emoji in starboards[guild_id][board_name]:
                if "channel_id" in starboards[guild_id][board_name][emoji]:
                    del starboards[guild_id][board_name][emoji]["channel_id"]
            save_starboards()
            await ctx.send(f"🧼 Removed output channel from starboard '{board_name}'.")

    else:
        await ctx.send("❌ Unknown subcommand.")


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

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    """Clears the specified number of recent messages in the current channel and logs it to #mod-logs."""
    if amount <= 0:
        await ctx.send("⚠️ Please specify a number greater than 0.")
        return

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command itself
        confirmation = await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.", delete_after=5)

        # Log to mod-logs channel
        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"🧾 **Message Clear**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Channel:** {ctx.channel.mention}\n"
                f"**Messages Deleted:** {len(deleted) - 1}"
            )
        else:
            print("[WARN] Could not find #mod-logs channel to log message deletions.")
        
        print(f"[DEBUG] {ctx.author} cleared {len(deleted) - 1} messages in #{ctx.channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages or access the mod-logs channel.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")


# List of roles that can be assigned or removed using the commands
ASSIGNABLE_ROLES = ["events", "d&d"]

@bot.command()
async def addrole(ctx, *, role_name: str):
    """Adds an allowed role to the user (users can add roles to themselves from the allowed list only)."""
    if role_name not in ASSIGNABLE_ROLES:
        await ctx.send(f"❌ You’re not allowed to assign the `{role_name}` role.")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found.")
        return

    if role in ctx.author.roles:
        await ctx.send(f"⚠️ You already have the `{role.name}` role.")
        return

    try:
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ Added `{role.name}` to you.")

        # Log to mod-logs
        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"➕ **Role Added**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**User:** {ctx.author.mention}\n"
                f"**Role:** `{role.name}`"
            )
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to assign that role.")

@bot.command()
async def removerole(ctx, *, role_name: str):
    """Removes an allowed role from the user (users can remove roles from themselves from the allowed list only)."""
    if role_name not in ASSIGNABLE_ROLES:
        await ctx.send(f"❌ You’re not allowed to remove the `{role_name}` role.")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found.")
        return

    if role not in ctx.author.roles:
        await ctx.send(f"⚠️ You don't have the `{role.name}` role.")
        return

    try:
        await ctx.author.remove_roles(role)
        await ctx.send(f"✅ Removed `{role.name}` from you.")

        # Log to mod-logs
        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"➖ **Role Removed**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**User:** {ctx.author.mention}\n"
                f"**Role:** `{role.name}`"
            )
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove that role.")

@bot.command()
async def viewroles(ctx):
    """Shows the list of roles that the user can assign or remove from themselves."""
    roles_list = ', '.join(ASSIGNABLE_ROLES)
    await ctx.send(f"✅ The roles you can assign or remove from yourself are: {roles_list}")

@bot.command(name="help")
async def help_command(ctx):
    # Create embed pages for different categories
    gif_commands = discord.Embed(
        title="📘 Help - GIF Management",
        description=(
            "**!showgifblockrole** - Shows currently blocked roles from sending GIFs\n"
            "**!setgifblockrole @Role** - Blocks GIFs from members with specified role\n"
            "**!removegifblockrole @Role** - Removes GIF block from specified role\n"
            "\n*Admins only* - These commands manage which roles are blocked from sending GIFs."
        ),
        color=discord.Color.red()
    )

    role_commands = discord.Embed(
        title="📘 Help - Role Management",
        description=(
            "**!addrole RoleName** - Adds an allowed role to yourself\n"
            "**!removerole RoleName** - Removes an allowed role from yourself\n"
            "**!viewroles** - Shows list of self-assignable roles\n"
            "\nAvailable roles: " + ", ".join(ASSIGNABLE_ROLES)
        ),
        color=discord.Color.green()
    )

    starboard_commands = discord.Embed(
        title="📘 Help - Starboard",
        description=(
            "**!starboard <name> create** - Creates new starboard\n"
            "**!starboard <name> delete** - Deletes starboard\n"
            "**!starboard <name> add reaction <emoji> <threshold>** - Adds reaction to starboard\n"
            "**!starboard <name> add channel <channel>** - Sets starboard channel\n"
            "**!starboard <name> remove reaction <emoji>** - Removes reaction\n"
            "**!starboard <name> remove channel** - Removes output channel\n"
            "**!viewstarboards** - Lists all starboards and their settings\n"
            "\n*Admins only* - Manages message highlight system."
        ),
        color=discord.Color.gold()
    )

    misc_commands = discord.Embed(
        title="📘 Help - Miscellaneous",
        description=(
            "**!clear <amount>** - Deletes specified number of messages\n"
            "**!help** - Shows this help message\n"
            "\n*Clear command requires admin permissions*"
        ),
        color=discord.Color.blue()
    )

    # Create a list of pages
    pages = [gif_commands, role_commands, starboard_commands, misc_commands]
    
    # Send the first page
    message = await ctx.send(embed=pages[0])

    # Add reactions for navigation
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    # Page navigation logic
    current_page = 0

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

    while True:
        try:
            # Wait for the user to react
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

            # Navigate the pages based on the reactions
            if str(reaction.emoji) == "➡️":
                current_page = (current_page + 1) % len(pages)
            elif str(reaction.emoji) == "⬅️":
                current_page = (current_page - 1) % len(pages)

            # Update the message with the new embed
            await message.edit(embed=pages[current_page])

            # Remove the reaction so the user can react again
            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            # If no reactions are received within the timeout period, stop the loop
            await message.clear_reactions()
            break

            
            
@bot.command()
@commands.has_permissions(administrator=True)
async def viewstarboards(ctx):
    """Lists all starboards and their settings in the server."""
    guild_id = str(ctx.guild.id)
    if guild_id not in starboards or not starboards[guild_id]:
        await ctx.send("❌ No starboards configured for this server.")
        return

    embed = discord.Embed(
        title=f"⭐ Starboards in {ctx.guild.name}",
        color=discord.Color.gold()
    )

    for board_name, settings in starboards[guild_id].items():
        board_info = []
        for emoji, emoji_settings in settings.items():
            channel = ctx.guild.get_channel(emoji_settings.get("channel_id", 0))
            channel_info = f"→ {channel.mention}" if channel else "→ *No channel set*"
            board_info.append(
                f"**{emoji}** (Threshold: {emoji_settings.get('threshold', 2)}) {channel_info}"
            )
        
        embed.add_field(
            name=f"📌 {board_name}",
            value="\n".join(board_info) if board_info else "No reactions configured",
            inline=False
        )

    await ctx.send(embed=embed)
# Add this at the top of your file (with other global variables)
starboard_messages = {}  # Format: {message_id: starboard_message_id}

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:
        return

    guild_id = str(payload.guild_id)
    if guild_id not in starboards:
        return

    for board_name, emoji_map in starboards[guild_id].items():
        emoji_str = str(payload.emoji)
        if emoji_str in emoji_map:
            threshold = emoji_map[emoji_str].get("threshold", 2)
            channel_id = emoji_map[emoji_str].get("channel_id")
            if not channel_id:
                print(f"[DEBUG] No channel configured for starboard '{board_name}' emoji '{emoji_str}'")
                return

            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            # Count reactions
            reaction_count = 0
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji_str:
                    users = [user async for user in reaction.users() if not user.bot]
                    reaction_count = len(users)
                    break

            if reaction_count < threshold:
                return

            target_channel = bot.get_channel(channel_id)
            db = get_db()

            # Check for existing entry
            cursor = db.cursor()
            cursor.execute(
                'SELECT starboard_msg_id FROM starboard_messages WHERE original_msg_id = ? AND guild_id = ?',
                (message.id, payload.guild_id)
            )
            existing = cursor.fetchone()

            # Prepare message content
            top_line = f"{emoji_str} **{reaction_count}** | https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            embed = discord.Embed(
                description=message.content or "No text",
                color=discord.Color.gold(),
                timestamp=message.created_at
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text="Original message sent")

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            if existing:
                try:
                    starboard_msg = await target_channel.fetch_message(existing['starboard_msg_id'])
                    await starboard_msg.edit(content=top_line, embed=embed)
                    print(f"[DEBUG] Updated starboard message for {message.author}")
                except discord.NotFound:
                    # Message was deleted, create new one
                    starboard_msg = await target_channel.send(content=top_line, embed=embed)
                    cursor.execute(
                        'UPDATE starboard_messages SET starboard_msg_id = ? WHERE original_msg_id = ? AND guild_id = ?',
                        (starboard_msg.id, message.id, payload.guild_id)
                    )
                    db.commit()
            else:
                starboard_msg = await target_channel.send(content=top_line, embed=embed)
                cursor.execute(
                    'INSERT INTO starboard_messages VALUES (?, ?, ?)',
                    (message.id, starboard_msg.id, payload.guild_id)
                )
                db.commit()
                
                # Handle URL previews only for new messages
                if message.content and ("http://" in message.content or "https://" in message.content):
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', message.content)
                    if urls:
                        await target_channel.send("\n".join(urls))

            print(f"[DEBUG] Starboard '{board_name}' triggered for message by {message.author}")
            db.close()  # Close connection after use


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
bot.run('token')
