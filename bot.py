import discord
from discord.ext import commands, tasks
from discord.ui import View, Select, Button
import os
from dotenv import load_dotenv
from database import Database
from datetime import datetime
import pytz
import io
from image_utils import create_stats_image

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='.', intents=intents)
db = Database()

EMBED_COLOR = 0xf9e6f0

# --- NEW: BOT READY EVENT AND ACTIVITY SETUP ---
@bot.event
async def on_ready():
    """
    Fires when the bot is ready. 
    Sets the bot's status/activity to "Playing kaori's ticket system".
    """
    print(f'Informational Bot is ready. Logged in as {bot.user}')

    # LINE 31: This sets the bot's status to "Playing kaori's ticket system"
    # To change the status type, modify the discord.Game() function.
    await bot.change_presence(activity=discord.Game(name="kaori's ticket system"))

    # NOTE: If you have background tasks (like weekly_reset_task), 
    # they should be started here, e.g., weekly_reset_task.start()

# --- END NEW CODE ---

ROLE_EMOJIS = {
    'owner': '<a:white_butterflies:1390909884928884886>',
    'co-owner': '<:piano_smile:1396035361091752080>',
    'head admin': '<:miffy_plush:1390909592543957063>',
    'admin': '<:miffy_plush:1390909592543957063>',
    'staff': '<a:cutebunny:1390853287347228914>',
    'trial staff': '<a:pink_bubbles:1396386164637958294>'
}

ROLE_ORDER = ['owner', 'co-owner', 'head admin', 'admin', 'staff', 'trial staff']
TRACKED_ROLE_IDS = [1390953916082028635, 1396008058693615678, 1428758437646307470]
PING_ROLE_ID = 1407881544202195004

STAFF_ROLE_HIERARCHY = {
    1390590641846878330: 'Owner',
    1396033952535285790: 'Co-Owner',
    1428181145899630785: 'Head Admin',
    1390954184530202624: 'Admin',
    1390954010650873918: 'Mod',
    1390953916082028635: 'Trial Mod',
    1395998827147952249: 'Lead MM',
    1390953447393722410: 'MM',
    1396008058693615678: 'Trial MM',
    1390953663694114878: 'Pilot',
    1428758437646307470: 'Trial Pilot'
}

async def has_staff_permission(member: discord.Member, guild_id: int) -> bool:
    staff_roles = await db.get_staff_roles(guild_id)
    if not staff_roles:
        return False
    return any(role.id in staff_roles for role in member.roles)

class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Middleman", value="middleman", emoji="<a:white_butterflies:1390909884928884886>"),
            discord.SelectOption(label="Pilot", value="pilot", emoji="<a:white_butterflies:1390909884928884886>"),
            discord.SelectOption(label="Verify", value="verify", emoji="<a:white_butterflies:1390909884928884886>"),
            discord.SelectOption(label="Giveaway", value="giveaway", emoji="<a:white_butterflies:1390909884928884886>"),
            discord.SelectOption(label="Other", value="other", emoji="<a:white_butterflies:1390909884928884886>")
        ]
        super().__init__(placeholder="Select a ticket category...", options=options, min_values=1, max_values=1, custom_id="ticket_category_select")
    
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        ticket_limit = await db.get_ticket_limit(interaction.guild.id)
        open_tickets = await db.get_open_ticket_count()
        
        if ticket_limit > 0 and open_tickets >= ticket_limit:
            await interaction.response.send_message(
                "TAIYO is currently at max tickets. Please try again later.",
                ephemeral=True
            )
            return
        
        ticket_number = await db.create_ticket(0, category, interaction.user.id)
        
        thread = await interaction.channel.create_thread(
            name=f"ticket-{ticket_number}",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=10080
        )
        
        await db.execute_raw(
            'UPDATE tickets SET channel_id = ? WHERE ticket_number = ?',
            (thread.id, ticket_number)
        )
        
        await thread.add_user(interaction.user)
        
        embed = discord.Embed(
            title=category.title(),
            description=f"welcome! <:castorice_shy:1439122834692767827>\nthank you for opening a ticket, staff will be here shortly\nplease be patient as you wait\n\nopened by {interaction.user.mention}",
            color=EMBED_COLOR
        )
        await thread.send(f"<@&{PING_ROLE_ID}>", embed=embed)
        
        await interaction.response.send_message(
            f"Ticket created! {thread.mention}",
            ephemeral=True
        )

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class ConfirmView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.value = None
        self.user_id = user_id
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your confirmation!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your confirmation!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

@bot.event
async def on_ready():
    await db.init_db()
    bot.add_view(TicketView())
    print(f'Bot is ready! Logged in as {bot.user}')
    if not weekly_reset_task.is_running():
        weekly_reset_task.start()
    if not sunday_leaderboard.is_running():
        sunday_leaderboard.start()

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    staff_role_id = PING_ROLE_ID
    
    before_has_role = any(role.id == staff_role_id for role in before.roles)
    after_has_role = any(role.id == staff_role_id for role in after.roles)
    
    if not before_has_role and after_has_role:
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()
        await db.update_role_assignment_date(after.id, timestamp)
        print(f"[DEBUG] Updated role assignment date for {after.name} (ID: {after.id})")

@bot.command()
async def sendticket(ctx):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    embed = discord.Embed(
        title="Create a Ticket",
        description="Select a category below to create a ticket.",
        color=EMBED_COLOR
    )
    
    view = TicketView()
    msg = await ctx.send(embed=embed, view=view)
    await db.set_ticket_message(ctx.guild.id, msg.id, ctx.channel.id)
    await ctx.message.delete()

@bot.command()
async def ticketlimit(ctx, limit: int):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    await db.set_ticket_limit(ctx.guild.id, limit)
    await ctx.send(f"Ticket limit set to {limit}!", delete_after=5)

@bot.command()
async def setarchive(ctx, channel: discord.TextChannel):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    await db.set_archive_channel(ctx.guild.id, channel.id)
    await ctx.send(f"Archive channel set to {channel.mention}!", delete_after=5)

@bot.command()
async def setleaderboard(ctx, channel: discord.TextChannel):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    await db.set_leaderboard_channel(ctx.guild.id, channel.id)
    await ctx.send(f"Leaderboard channel set to {channel.mention}!", delete_after=5)

@bot.command()
async def setstaffroles(ctx, *roles: discord.Role):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    if not roles:
        await ctx.send("Please provide at least one role!", delete_after=5)
        return
    
    role_ids = ','.join(str(role.id) for role in roles)
    await db.set_staff_roles(ctx.guild.id, role_ids)
    role_mentions = ' '.join(role.mention for role in roles)
    await ctx.send(f"Staff roles set to: {role_mentions}", delete_after=5)

@bot.command()
async def setroles(ctx, role_type: str, *roles: discord.Role):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can use this command!", delete_after=5)
        return
    
    valid_types = ['admin', 'owner', 'moderator', 'staff']
    if role_type.lower() not in valid_types:
        await ctx.send(f"Invalid role type! Valid types: {', '.join(valid_types)}", delete_after=5)
        return
    
    if not roles:
        await ctx.send("Please provide at least one role!", delete_after=5)
        return
    
    role_ids = ','.join(str(role.id) for role in roles)
    
    if role_type.lower() == 'staff':
        await db.set_staff_roles(ctx.guild.id, role_ids)
    else:
        await db.set_role_type(ctx.guild.id, role_type.lower(), role_ids)
    
    role_mentions = ' '.join(role.mention for role in roles)
    await ctx.send(f"{role_type.title()} roles set to: {role_mentions}", delete_after=5)

@bot.command()
async def claim(ctx, force: str = ""):
    if not isinstance(ctx.channel, discord.Thread):
        return
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        return
    
    if force == "force":
        if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
            return
        
        if ticket_info['handler_id']:
            await db.unclaim_ticket(ctx.channel.id)
    else:
        if not await has_staff_permission(ctx.author, ctx.guild.id):
            return
    
    await db.claim_ticket(ctx.channel.id, ctx.author.id)
    
    embed = discord.Embed(
        description=f"{ctx.author.mention} has claimed the ticket",
        color=EMBED_COLOR
    )
    
    msg = await ctx.send(embed=embed, reference=ctx.message)
    await ctx.message.delete()

@bot.command()
async def unclaim(ctx, force: str = ""):
    if not isinstance(ctx.channel, discord.Thread):
        return

    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        return

    if force == "force":
        if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
            return

    else:
        if not await has_staff_permission(ctx.author, ctx.guild.id):
            return

        if ticket_info['handler_id'] != ctx.author.id:
            return

    await db.unclaim_ticket(ctx.channel.id)



    embed = discord.Embed(
        description=f"{ctx.author.mention} has unclaimed this ticket",
        color=0xc5bdff

    )

    await ctx.send(embed=embed, reference=ctx.message)

    await ctx.message.delete()

@bot.command()
async def close(ctx, *, reason: str = "No reason provided"):
    if not isinstance(ctx.channel, discord.Thread):
        return
    
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        await ctx.send("This is not a valid ticket thread!")
        return
    
    handler = await bot.fetch_user(ticket_info['handler_id']) if ticket_info['handler_id'] else None
    credit_text = handler.mention if handler else "No one"
    
    confirmation_embed = discord.Embed(
        title="Ticket Confirmation",
        description="are you sure you want to close?",
        color=EMBED_COLOR
    )
    confirmation_embed.add_field(name="Credit given:", value=credit_text, inline=False)
    
    view = ConfirmView(ctx.author.id)
    msg = await ctx.send(embed=confirmation_embed, view=view)
    
    await view.wait()
    
    if not view.value:
        await msg.edit(content="Ticket close cancelled.", view=None, embed=None)
        return
    
    await db.close_ticket(ctx.channel.id, ctx.author.id, reason)
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        await msg.edit(content="Error: Could not retrieve ticket information.", view=None)
        return
    
    messages = []
    async for message in ctx.channel.history(limit=None, oldest_first=True):
        messages.append(message)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ticket #{ticket_info['ticket_number']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #36393f; color: #dcddde; }}
        .message {{ margin: 10px 0; padding: 10px; background: #40444b; border-radius: 5px; }}
        .author {{ color: #7289da; font-weight: bold; }}
        .timestamp {{ color: #72767d; font-size: 0.8em; }}
    </style>
</head>
<body>
    <h1>Ticket #{ticket_info['ticket_number']}</h1>
"""
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content.replace('<', '&lt;').replace('>', '&gt;')
        html_content += f'    <div class="message"><span class="author">{msg.author}</span> <span class="timestamp">{timestamp}</span><br>{content}</div>\n'
    
    html_content += "</body>\n</html>"
    created_at = datetime.fromisoformat(ticket_info['created_at'])
    closed_at = datetime.fromisoformat(ticket_info['closed_at'])
    
    opener = await bot.fetch_user(ticket_info['opener_id'])
    handler = await bot.fetch_user(ticket_info['handler_id']) if ticket_info['handler_id'] else None
    closer = await bot.fetch_user(ticket_info['closer_id'])
    
    created_timestamp = int(created_at.timestamp())
    closed_timestamp = int(closed_at.timestamp())
    
    archive_channel_id = await db.get_archive_channel(ctx.guild.id)
    if archive_channel_id:
        archive_channel = bot.get_channel(archive_channel_id)
        if archive_channel:
            embed_description = f"""Ticket #{ticket_info['ticket_number']}
opened by       closed by         handled by
{opener.mention}                   {closer.mention}                {handler.mention if handler else 'None'}
opened at
<t:{created_timestamp}:F>
closed at
<t:{closed_timestamp}:F>
reason
{reason}"""
            
            transcript_embed = discord.Embed(
                description=embed_description,
                color=EMBED_COLOR
            )
            
            file = discord.File(io.BytesIO(html_content.encode()), filename=f"ticket #{ticket_info['ticket_number']}.html")
            
            button_view = View()
            button_view.add_item(Button(label="View Thread", url=ctx.channel.jump_url))
            
            await archive_channel.send(embed=transcript_embed, file=file, view=button_view)
    
    try:
        dm_description = f"""Ticket #{ticket_info['ticket_number']}
opened by       <:whitedash:1390902298166820996>        closed by       <:whitedash:1390902298166820996>          handled by
{opener.mention}                                      {closer.mention}                               {handler.mention if handler else 'None'}
opened at
<t:{created_timestamp}:F>
closed at
<t:{closed_timestamp}:F>
reason
{reason}"""
        
        dm_embed = discord.Embed(
            description=dm_description,
            color=EMBED_COLOR
        )
        
        dm_button_view = View()
        dm_button_view.add_item(Button(label="View Thread", url=ctx.channel.jump_url))
        
        dm_file = discord.File(io.BytesIO(html_content.encode()), filename=f"ticket #{ticket_info['ticket_number']}.html")
        await opener.send(embed=dm_embed, file=dm_file, view=dm_button_view)
    except:
        pass
    
    close_embed = discord.Embed(
        title=f"ticket closed <a:Heart:1396388971818520576>",
        description=f"this ticket was closed by {ctx.author.mention}\n\n**reason:**\n{reason}",
        color=EMBED_COLOR
    )
    
    await msg.edit(embed=close_embed, view=None)
    await ctx.channel.edit(archived=True, locked=True)

@bot.command()
async def fm(ctx):
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    messages = []
    async for message in ctx.channel.history(limit=1, oldest_first=True):
        messages.append(message)
    
    if messages:
        first_msg = messages[0]
        embed = discord.Embed(
            description=f"First message sent in {ctx.channel.mention} - [here]({first_msg.jump_url})",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

@bot.command()
async def add(ctx, member: discord.Member):
    if not isinstance(ctx.channel, discord.Thread):
        return
    
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    await ctx.channel.add_user(member)
    await ctx.send(f"Added {member.mention} to the thread!")

@bot.command()
async def remove(ctx, member: discord.Member):
    if not isinstance(ctx.channel, discord.Thread):
        return
    
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    await ctx.channel.remove_user(member)
    await ctx.send(f"Removed {member.mention} from the thread!")

@bot.command()
async def rename(ctx, *, name: str):
    if not isinstance(ctx.channel, discord.Thread):
        return
    
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    print(f"[DEBUG] Rename command called by {ctx.author} to '{name}'")
    await ctx.channel.edit(name=name)

@bot.command()
async def profile(ctx, action: str = "", *, message: str = ""):
    if action == "edit":
        if not await has_staff_permission(ctx.author, ctx.guild.id):
            return
        
        if not message:
            return
        
        await db.update_profile_message(ctx.author.id, message)
        await ctx.send("Profile message updated!")
    else:
        return

@bot.command()
async def stats(ctx, member: discord.Member = None):
    print(f"[DEBUG] Stats command called by {ctx.author} for {member}")
    if member is None:
        member = ctx.author
    
    stats = await db.get_user_stats(member.id)
    
    banner_url = None
    if member.banner:
        banner_url = member.banner.url
    
    avatar_url = member.display_avatar.url
    
    highest_role = None
    for role_id in STAFF_ROLE_HIERARCHY.keys():
        role = ctx.guild.get_role(role_id)
        if role and role in member.roles:
            highest_role = STAFF_ROLE_HIERARCHY[role_id]
            break
    
    ping_role = ctx.guild.get_role(PING_ROLE_ID)
    join_date = None
    if ping_role and ping_role in member.roles:
        role_assignment_date = stats.get('role_assignment_date')
        if role_assignment_date and role_assignment_date != 'N/A':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(role_assignment_date)
                timestamp_int = int(dt.timestamp())
                join_date = f"<t:{timestamp_int}:D>"
            except:
                join_date = role_assignment_date
        else:
            join_date = "N/A"
    
    image_data = await create_stats_image(member, banner_url, avatar_url, member.name, join_date)
    
    embed = discord.Embed(
        title=f"{member.name}",
        description=stats.get('profile_message', ''),
        color=EMBED_COLOR
    )
    
    rank_value = highest_role if highest_role else "N/A"
    closed_total = stats['all_time_closed']
    closed_7d = stats['weekly_closed']
    handled_total = stats['all_time_handled']
    handled_7d = stats['weekly_handled']
    
    embed.add_field(name="Rank", value=rank_value, inline=True)
    embed.add_field(name="Closed Total", value=str(closed_total), inline=True)
    embed.add_field(name="Closed 7d", value=str(closed_7d), inline=True)
    
    embed.add_field(name="Join Date", value=join_date if join_date else "N/A", inline=True)
    embed.add_field(name="Handled Total", value=str(handled_total), inline=True)
    embed.add_field(name="Handled 7d", value=str(handled_7d), inline=True)
    
    embed.set_image(url="attachment://stats.png")
    
    file = discord.File(image_data, filename="stats.png")
    await ctx.send(embed=embed, file=file)

@bot.command()
async def lb(ctx, subcommand: str = "", member: discord.Member = None, role: str = ""):
    print(f"[DEBUG] LB command called by {ctx.author} with subcommand '{subcommand}'")
    if subcommand == "add":
        if not any(r.name.lower() in ['admin', 'mod', 'moderator'] for r in ctx.author.roles):
            return
        
        if not member or not role:
            return
        
        role_lower = role.lower()
        if role_lower not in ROLE_ORDER:
            return
        
        await db.add_leaderboard_role(member.id, role_lower)
        await ctx.send(f"Added {member.mention} to {role_lower} leaderboard!")
        return
    
    elif subcommand == "remove":
        if not any(r.name.lower() in ['admin', 'mod', 'moderator'] for r in ctx.author.roles):
            return
        
        if not member or not role:
            return
        
        role_lower = role.lower()
        await db.remove_leaderboard_role(member.id, role_lower)
        await ctx.send(f"Removed {member.mention} from {role_lower} leaderboard!")
        return
    
    elif subcommand == "w":
        await show_leaderboard(ctx, "weekly", "handled")
        return
    
    elif subcommand == "c":
        await show_leaderboard(ctx, "all_time", "closed")
        return
    
    elif subcommand == "cw":
        await show_leaderboard(ctx, "weekly", "closed")
        return
    
    else:
        await show_leaderboard(ctx, "all_time", "handled")

async def show_leaderboard(ctx, timeframe: str, stat_type: str):
    if not await has_staff_permission(ctx.author, ctx.guild.id):
        return
    
    leaderboard_data = await db.get_leaderboard_data(
        'weekly' if timeframe == 'weekly' else ('all_time_closed' if stat_type == 'closed' else 'all_time')
    )
    
    user_roles = {}
    for user_id, all_handled, all_closed, week_handled, week_closed in leaderboard_data:
        lb_role = await db.get_user_leaderboard_role(user_id)
        if lb_role:
            if lb_role not in user_roles:
                user_roles[lb_role] = []
            
            if timeframe == 'weekly':
                if stat_type == 'closed':
                    total = week_closed
                    weekly_stat = week_closed
                else:
                    total = week_handled
                    weekly_stat = week_handled
                user_roles[lb_role].append((user_id, all_handled, weekly_stat, total))
            else:
                if stat_type == 'closed':
                    total = all_closed
                    weekly_stat = week_closed
                else:
                    total = all_handled
                    weekly_stat = week_handled
                user_roles[lb_role].append((user_id, total, weekly_stat, total))
    
    for role in user_roles:
        user_roles[role].sort(key=lambda x: x[3], reverse=True)
    
    if stat_type == 'closed':
        title = "closed leaderboard 𐙚 ‧₊˚ ⋅"
    else:
        title = "leaderboard 𐙚 ‧₊˚ ⋅"
    
    description = ""
    for role in ROLE_ORDER:
        if role in user_roles and user_roles[role]:
            emoji = ROLE_EMOJIS.get(role, "")
            description += f"\n{emoji} {role}\n"
            
            for user_id, all_time_stat, weekly_stat, _ in user_roles[role]:
                description += f"<@{user_id}> **{all_time_stat}** all - **{weekly_stat}** 7d\n"
    
    if not description:
        description = "No leaderboard data available."
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def modify(ctx, member: discord.Member, stat: str, value: int):
    if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
        return
    
    valid_stats = ['wclosed', 'whandled', 'closed', 'handled']
    if stat.lower() not in valid_stats:
        return
    
    stat_map = {
        'wclosed': 'weekly_closed',
        'whandled': 'weekly_handled',
        'closed': 'all_time_closed',
        'handled': 'all_time_handled'
    }
    
    await db.modify_stats(member.id, stat_map[stat.lower()], value)
    await ctx.send(f"Modified {member.mention}'s {stat} by {value}!")

@bot.command()
async def resetweekly(ctx):
    print(f"[DEBUG] resetweekly called by {ctx.author}")
    print(f"[DEBUG] User roles: {[role.name for role in ctx.author.roles]}")
    
    if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
        print(f"[DEBUG] User {ctx.author} doesn't have admin/mod/moderator role")
        await ctx.send("You don't have permission to use this command!", ephemeral=True)
        return
    
    print(f"[DEBUG] Resetting weekly stats...")
    await db.reset_weekly_stats()
    print(f"[DEBUG] Weekly stats reset complete")
    
    embed = discord.Embed(
        description="weekly successfully reseted!",
        color=EMBED_COLOR
    )
    await ctx.send(embed=embed, delete_after=5)

@tasks.loop(hours=1)
async def weekly_reset_task():
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    
    if now.weekday() == 6 and now.hour == 4:
        await db.reset_weekly_stats()
        print("Weekly stats reset!")

@tasks.loop(hours=1)
async def sunday_leaderboard():
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    
    if now.weekday() == 6 and now.hour == 4:
        for guild in bot.guilds:
            lb_channel_id = await db.get_leaderboard_channel(guild.id)
            if lb_channel_id:
                channel = bot.get_channel(lb_channel_id)
                if channel:
                    all_time_data = await build_leaderboard_embed("all_time", "handled")
                    weekly_data = await build_leaderboard_embed("weekly", "handled")
                    
                    await channel.send(embed=all_time_data)
                    await channel.send(embed=weekly_data)

async def build_leaderboard_embed(timeframe: str, stat_type: str):
    leaderboard_data = await db.get_leaderboard_data(
        'weekly' if timeframe == 'weekly' else 'all_time'
    )
    
    user_roles = {}
    for user_id, all_handled, all_closed, week_handled, week_closed in leaderboard_data:
        lb_role = await db.get_user_leaderboard_role(user_id)
        if lb_role:
            if lb_role not in user_roles:
                user_roles[lb_role] = []
            
            if timeframe == 'weekly':
                total = week_handled + week_closed
                user_roles[lb_role].append((user_id, all_handled + all_closed, week_handled + week_closed, total))
            else:
                total = all_handled + all_closed
                user_roles[lb_role].append((user_id, total, week_handled + week_closed, total))
    
    for role in user_roles:
        user_roles[role].sort(key=lambda x: x[3], reverse=True)
    
    title = "𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃 𐙚 ‧₊˚ ⋅" if timeframe == "all_time" else "𝐖𝐄𝐄𝐊𝐋𝐘 𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃 𐙚 ‧₊˚ ⋅"
    
    description = ""
    for role in ROLE_ORDER:
        if role in user_roles and user_roles[role]:
            emoji = ROLE_EMOJIS.get(role, "")
            description += f"\n{emoji} {role}\n"
            
            for user_id, all_time_stat, weekly_stat, _ in user_roles[role]:
                description += f"<@{user_id}> **{all_time_stat}** all - **{weekly_stat}** 7d\n"
    
    if not description:
        description = "No leaderboard data available."
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )
    
    return embed

bot.run(os.getenv('DISCORD_TOKEN'))