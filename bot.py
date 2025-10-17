import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Select, Button
import os
from dotenv import load_dotenv
from database import Database
from datetime import datetime, timedelta
import pytz
import asyncio
from typing import Optional
import io
from PIL import Image, ImageDraw, ImageFilter
import aiohttp
from image_utils import create_stats_image

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='.', intents=intents)
db = Database()

EMBED_COLOR = 0xf9e6f0

ROLE_EMOJIS = {
    'owner': '<a:white_butterflies:1390909884928884886>',
    'co-owner': '<:piano_smile:1396035361091752080>',
    'admin': '<:miffy_plush:1390909592543957063>',
    'staff': '<a:cutebunny:1390853287347228914>',
    'trial': '<a:pink_bubbles:1396386164637958294>'
}

ROLE_ORDER = ['owner', 'co-owner', 'admin', 'staff', 'trial']

class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Middleman", value="middleman", emoji="🤝"),
            discord.SelectOption(label="Pilot", value="pilot", emoji="✈️"),
            discord.SelectOption(label="Verify", value="verify", emoji="✅"),
            discord.SelectOption(label="Giveaway", value="giveaway", emoji="🎁"),
            discord.SelectOption(label="Other", value="other", emoji="❓")
        ]
        super().__init__(placeholder="Select a ticket category...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        ticket_limit = await db.get_ticket_limit(interaction.guild.id)
        open_tickets = await db.get_open_ticket_count()
        
        if ticket_limit > 0 and open_tickets >= ticket_limit:
            await interaction.response.send_message(
                "Tickets are currently full. try again later!",
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
            title=f"Ticket #{ticket_number}",
            description=f"Category: **{category.title()}**\nOpened by: {interaction.user.mention}",
            color=EMBED_COLOR
        )
        await thread.send(embed=embed)
        
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
    print(f'Bot is ready! Logged in as {bot.user}')
    weekly_reset_task.start()
    sunday_leaderboard.start()

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
async def claim(ctx, force: str = None):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in ticket threads!")
        return
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        await ctx.send("This is not a valid ticket thread!")
        return
    
    if force == "force":
        if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
            await ctx.send("You don't have permission to force claim!")
            return
        
        if ticket_info['handler_id']:
            await db.unclaim_ticket(ctx.channel.id)
    
    await db.claim_ticket(ctx.channel.id, ctx.author.id)
    await ctx.send(f"{ctx.author.mention} has claimed this ticket!")

@bot.command()
async def unclaim(ctx, force: str = None):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in ticket threads!")
        return
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        await ctx.send("This is not a valid ticket thread!")
        return
    
    if force == "force":
        if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
            await ctx.send("You don't have permission to force unclaim!")
            return
    elif ticket_info['handler_id'] != ctx.author.id:
        await ctx.send("You haven't claimed this ticket!")
        return
    
    await db.unclaim_ticket(ctx.channel.id)
    await ctx.send("Ticket has been unclaimed!")

@bot.command()
async def close(ctx, *, reason: str = "No reason provided"):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in ticket threads!")
        return
    
    if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to close tickets!")
        return
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    if not ticket_info:
        await ctx.send("This is not a valid ticket thread!")
        return
    
    view = ConfirmView(ctx.author.id)
    msg = await ctx.send(f"Are you sure you want to close this ticket?\nReason: {reason}", view=view)
    
    await view.wait()
    
    if not view.value:
        await msg.edit(content="Ticket close cancelled.", view=None)
        return
    
    await db.close_ticket(ctx.channel.id, ctx.author.id, reason)
    
    messages = []
    async for message in ctx.channel.history(limit=None, oldest_first=True):
        messages.append(message)
    
    transcript_text = ""
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript_text += f"[{timestamp}] {msg.author}: {msg.content}\n"
    
    ticket_info = await db.get_ticket_info(ctx.channel.id)
    created_at = datetime.fromisoformat(ticket_info['created_at'])
    closed_at = datetime.fromisoformat(ticket_info['closed_at'])
    duration = closed_at - created_at
    
    opener = await bot.fetch_user(ticket_info['opener_id'])
    handler = await bot.fetch_user(ticket_info['handler_id']) if ticket_info['handler_id'] else None
    closer = await bot.fetch_user(ticket_info['closer_id'])
    
    archive_channel_id = await db.get_archive_channel(ctx.guild.id)
    if archive_channel_id:
        archive_channel = bot.get_channel(archive_channel_id)
        if archive_channel:
            transcript_embed = discord.Embed(
                title=f"Ticket #{ticket_info['ticket_number']} Transcript",
                color=EMBED_COLOR
            )
            transcript_embed.add_field(name="Opener", value=opener.mention, inline=True)
            transcript_embed.add_field(name="Handler", value=handler.mention if handler else "None", inline=True)
            transcript_embed.add_field(name="Closer", value=closer.mention, inline=True)
            transcript_embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            transcript_embed.add_field(name="Closed At", value=closed_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            transcript_embed.add_field(name="Duration", value=str(duration), inline=True)
            transcript_embed.add_field(name="Close Reason", value=reason, inline=False)
            
            file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"ticket-{ticket_info['ticket_number']}.txt")
            
            button_view = View()
            button_view.add_item(Button(label="View Thread", url=ctx.channel.jump_url))
            
            await archive_channel.send(embed=transcript_embed, file=file, view=button_view)
    
    try:
        dm_embed = discord.Embed(
            title=f"Ticket #{ticket_info['ticket_number']} Closed",
            description=f"Your ticket has been closed.\n**Reason:** {reason}",
            color=EMBED_COLOR
        )
        dm_embed.add_field(name="Handler", value=handler.mention if handler else "None", inline=True)
        dm_embed.add_field(name="Closer", value=closer.mention, inline=True)
        dm_embed.add_field(name="Duration", value=str(duration), inline=True)
        
        dm_button_view = View()
        dm_button_view.add_item(Button(label="View Thread", url=ctx.channel.jump_url))
        
        dm_file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"ticket-{ticket_info['ticket_number']}.txt")
        await opener.send(embed=dm_embed, file=dm_file, view=dm_button_view)
    except:
        pass
    
    await msg.edit(content=f"Ticket closed! Transcript saved.", view=None)
    await ctx.channel.edit(archived=True, locked=True)

@bot.command()
async def fm(ctx):
    if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command!")
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
        await ctx.send("This command can only be used in threads!")
        return
    
    if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command!")
        return
    
    await ctx.channel.add_user(member)
    await ctx.send(f"Added {member.mention} to the thread!")

@bot.command()
async def remove(ctx, member: discord.Member):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in threads!")
        return
    
    if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command!")
        return
    
    await ctx.channel.remove_user(member)
    await ctx.send(f"Removed {member.mention} from the thread!")

@bot.command()
async def rename(ctx, *, name: str):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in threads!")
        return
    
    if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command!")
        return
    
    await ctx.channel.edit(name=name)
    await ctx.send(f"Thread renamed to {name}!")

@bot.command()
async def profile(ctx, action: str = None, *, message: str = None):
    if action == "edit":
        if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
            await ctx.send("You don't have permission to edit your profile!")
            return
        
        if not message:
            await ctx.send("Please provide a profile message!")
            return
        
        await db.update_profile_message(ctx.author.id, message)
        await ctx.send("Profile message updated!")
    else:
        await ctx.send("Usage: `.profile edit <message>`")

@bot.command()
async def stats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    stats = await db.get_user_stats(member.id)
    lb_role = await db.get_user_leaderboard_role(member.id)
    
    banner_url = None
    if member.banner:
        banner_url = member.banner.url
    
    avatar_url = member.display_avatar.url
    
    image_data = await create_stats_image(member, banner_url, avatar_url)
    
    embed = discord.Embed(
        title=f"{member.name}'s Stats",
        color=EMBED_COLOR
    )
    
    total_all_time = stats['all_time_handled'] + stats['all_time_closed']
    total_weekly = stats['weekly_handled'] + stats['weekly_closed']
    
    embed.add_field(name="All-Time Stats", value=f"Handled: {stats['all_time_handled']}\nClosed: {stats['all_time_closed']}\nTotal: {total_all_time}", inline=True)
    embed.add_field(name="Weekly Stats", value=f"Handled: {stats['weekly_handled']}\nClosed: {stats['weekly_closed']}\nTotal: {total_weekly}", inline=True)
    
    if lb_role:
        embed.add_field(name="Rank", value=lb_role.title(), inline=True)
    
    if stats['role_assignment_date']:
        embed.add_field(name="Role Assignment Date", value=stats['role_assignment_date'], inline=True)
    
    if stats['profile_message']:
        embed.add_field(name="Profile Message", value=stats['profile_message'], inline=False)
    
    embed.set_image(url="attachment://stats.png")
    
    file = discord.File(image_data, filename="stats.png")
    await ctx.send(embed=embed, file=file)

@bot.command()
async def lb(ctx, subcommand: str = None, member: discord.Member = None, role: str = None):
    if subcommand == "add":
        if not any(r.name.lower() in ['admin', 'mod', 'moderator'] for r in ctx.author.roles):
            await ctx.send("You don't have permission to use this command!")
            return
        
        if not member or not role:
            await ctx.send("Usage: `.lb add @user role`")
            return
        
        role_lower = role.lower()
        if role_lower not in ROLE_ORDER:
            await ctx.send(f"Invalid role! Valid roles: {', '.join(ROLE_ORDER)}")
            return
        
        await db.add_leaderboard_role(member.id, role_lower)
        await ctx.send(f"Added {member.mention} to {role_lower} leaderboard!")
        return
    
    elif subcommand == "remove":
        if not any(r.name.lower() in ['admin', 'mod', 'moderator'] for r in ctx.author.roles):
            await ctx.send("You don't have permission to use this command!")
            return
        
        if not member or not role:
            await ctx.send("Usage: `.lb remove @user role`")
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
    if not any(role.name.lower() in ['admin', 'mod', 'moderator', 'staff'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to view the leaderboard!")
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
                else:
                    total = week_handled + week_closed
                weekly_stat = week_closed if stat_type == 'closed' else week_handled + week_closed
                user_roles[lb_role].append((user_id, all_handled + all_closed if stat_type != 'closed' else all_closed, weekly_stat, total))
            else:
                if stat_type == 'closed':
                    total = all_closed
                else:
                    total = all_handled + all_closed
                weekly_stat = week_closed if stat_type == 'closed' else week_handled + week_closed
                user_roles[lb_role].append((user_id, total, weekly_stat, total))
    
    for role in user_roles:
        user_roles[role].sort(key=lambda x: x[3], reverse=True)
    
    if stat_type == 'closed':
        title = "*##closed leaderboard* 𐙚 ‧₊˚ ⋅"
    else:
        title = "*##leaderboard* 𐙚 ‧₊˚ ⋅"
    
    description = ""
    for role in ROLE_ORDER:
        if role in user_roles and user_roles[role]:
            emoji = ROLE_EMOJIS.get(role, "")
            description += f"\n{emoji} {role}\n"
            
            for user_id, all_time_stat, weekly_stat, _ in user_roles[role]:
                try:
                    user = await bot.fetch_user(user_id)
                    description += f"@{user.name} **{all_time_stat}** all - **{weekly_stat}** 7d\n"
                except:
                    description += f"<@{user_id}> **{all_time_stat}** all - **{weekly_stat}** 7d\n"
    
    if not description:
        description = "No leaderboard data available."
    
    embed = discord.Embed(
        description=title + description,
        color=EMBED_COLOR
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def modify(ctx, member: discord.Member, stat: str, value: int):
    if not any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command!")
        return
    
    valid_stats = ['wclosed', 'whandled', 'closed', 'handled']
    if stat.lower() not in valid_stats:
        await ctx.send(f"Invalid stat! Valid stats: {', '.join(valid_stats)}")
        return
    
    stat_map = {
        'wclosed': 'weekly_closed',
        'whandled': 'weekly_handled',
        'closed': 'all_time_closed',
        'handled': 'all_time_handled'
    }
    
    await db.modify_stats(member.id, stat_map[stat.lower()], value)
    await ctx.send(f"Modified {member.mention}'s {stat} by {value}!")

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
    
    title = "*##leaderboard* 𐙚 ‧₊˚ ⋅" if timeframe == "all_time" else "*##weekly leaderboard* 𐙚 ‧₊˚ ⋅"
    
    description = ""
    for role in ROLE_ORDER:
        if role in user_roles and user_roles[role]:
            emoji = ROLE_EMOJIS.get(role, "")
            description += f"\n{emoji} {role}\n"
            
            for user_id, all_time_stat, weekly_stat, _ in user_roles[role]:
                try:
                    user = await bot.fetch_user(user_id)
                    description += f"@{user.name} **{all_time_stat}** all - **{weekly_stat}** 7d\n"
                except:
                    description += f"<@{user_id}> **{all_time_stat}** all - **{weekly_stat}** 7d\n"
    
    if not description:
        description = "No leaderboard data available."
    
    embed = discord.Embed(
        description=title + description,
        color=EMBED_COLOR
    )
    
    return embed

bot.run(os.getenv('DISCORD_TOKEN'))
