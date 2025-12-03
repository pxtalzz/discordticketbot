# Quick Setup Guide

Your Discord bot is **running and ready**! Follow these steps to set it up in your server.

## Step 1: Invite the Bot to Your Server

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Go to **OAuth2** → **URL Generator**
4. Select scopes: `bot` and `applications.commands`
5. Select bot permissions:
   - Manage Threads
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Manage Messages
6. Copy the generated URL and open it in your browser
7. Select your server and authorize the bot

## Step 2: Configure Your Server

Run these commands in your Discord server (you must be the server owner):

### 1. Set up the ticket creation channel
```
.sendticket
```
This creates the persistent ticket dropdown menu. Members will select a category here to create tickets.

### 2. Set the archive channel
```
.setarchive #archive-channel
```
Replace `#archive-channel` with your archive channel mention. All ticket transcripts will be posted here.

### 3. Set the leaderboard channel
```
.setleaderboard #leaderboard-channel
```
Replace `#leaderboard-channel` with your leaderboard channel mention. Weekly leaderboards will auto-post here every Sunday at 4 AM EST.

### 4. Set ticket limit (optional)
```
.ticketlimit 10
```
This limits open tickets to 10. Adjust the number as needed. Set to 0 for unlimited tickets.

## Step 3: Add Staff to Leaderboard

Add your staff members to the leaderboard with their appropriate roles:

```
.lb add @username owner
.lb add @username co-owner
.lb add @username admin
.lb add @username staff
.lb add @username trial
```

Valid roles: `owner`, `co-owner`, `admin`, `staff`, `trial`

## Available Commands

### Owner Only
- `.sendticket` - Post ticket creation message
- `.ticketlimit <number>` - Set max open tickets
- `.setarchive #channel` - Set archive channel
- `.setleaderboard #channel` - Set leaderboard channel

### Admin/Mod Only
- `.close <reason>` - Close ticket with reason
- `.claim force` - Force claim a ticket
- `.unclaim force` - Force unclaim a ticket
- `.modify @user <stat> <value>` - Modify user stats
  - Stats: `wclosed`, `whandled`, `closed`, `handled`
- `.lb add @user <role>` - Add user to leaderboard
- `.lb remove @user <role>` - Remove user from leaderboard

### Staff Commands
- `.claim` - Claim a ticket
- `.unclaim` - Unclaim a ticket
- `.fm` - Jump to first message
- `.add @user` - Add user to thread
- `.remove @user` - Remove user from thread
- `.rename <name>` - Rename thread
- `.profile edit <message>` - Set profile message
- `.stats [@user]` - View stats (with profile image)
- `.lb` - All-time leaderboard
- `.lb w` - Weekly leaderboard
- `.lb c` - All-time closes leaderboard
- `.lb cw` - Weekly closes leaderboard

## Features

✅ **Ticket System**
- 5 categories: Middleman, Pilot, Verify, Giveaway, Other
- Automatic ticket numbering
- Ticket limits with "tickets full" notification
- Private thread creation

✅ **Ticket Management**
- Claim/unclaim with credit tracking
- Close with confirmation and reason
- Full transcripts with timestamps
- Archive posting with embed
- DM to ticket opener with transcript

✅ **Statistics**
- All-time and weekly tracking
- Handled and closed counts
- Custom profile messages
- 885x303px profile image with banner/avatar

✅ **Leaderboards**
- Role-based hierarchy display
- Custom emojis for each role
- Only shows sections with members
- Weekly auto-posting (Sunday 4 AM EST)
- Automatic weekly reset

## Automation

The bot automatically:
- Resets weekly stats every **Sunday at 4 AM EST**
- Posts leaderboards every **Sunday at 4 AM EST**
- Tracks all ticket actions for statistics
- Generates transcripts on ticket close
- Sends DMs to ticket openers

## Need Help?

- Check `README.md` for detailed documentation
- Check `IMPLEMENTATION.md` for technical details
- All data is stored in `bot_data.db` (SQLite database)

## Bot Status

Current Status: **✅ Running as "kirei#2389"**

Enjoy your Discord ticket and stats bot! 🎉
