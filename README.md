<<<<<<< HEAD
# discordticketbot
kaori
=======
# Discord Ticket & Stats Bot

A comprehensive Discord bot for managing tickets, tracking staff statistics, and displaying leaderboards.

## Features

### Ticket System
- **Category Selection**: Create tickets via dropdown (Middleman, Pilot, Verify, Giveaway, Other)
- **Automatic Numbering**: Sequential ticket numbers for organization
- **Ticket Limits**: Set maximum open tickets with `.ticketlimit`
- **Claim/Unclaim System**: Staff can claim tickets for credit tracking
- **Close with Transcripts**: Archive tickets with full transcripts and DM to opener
- **Archive Channel**: Automatic transcript posting with embed summaries

### Staff Commands
- `.sendticket` - Post persistent ticket creation message (owner only)
- `.ticketlimit <number>` - Set maximum open tickets (owner only)
- `.setarchive #channel` - Set archive channel for transcripts (owner only)
- `.setleaderboard #channel` - Set channel for weekly leaderboard posts (owner only)
- `.claim` / `.claim force` - Claim a ticket
- `.unclaim` / `.unclaim force` - Unclaim a ticket
- `.close <reason>` - Close ticket with reason and transcript
- `.fm` - Jump to first message in thread/channel
- `.add @user` - Add user to thread
- `.remove @user` - Remove user from thread
- `.rename <name>` - Rename thread
- `.profile edit <message>` - Set custom profile message
- `.stats [@user]` - View user statistics with profile image
- `.lb` - View all-time leaderboard (handles)
- `.lb w` - View weekly leaderboard (handles)
- `.lb c` - View all-time closes leaderboard
- `.lb cw` - View weekly closes leaderboard
- `.lb add @user <role>` - Add user to leaderboard role
- `.lb remove @user <role>` - Remove user from leaderboard role
- `.modify @user <stat> <value>` - Modify user statistics
  - Stats: `wclosed`, `whandled`, `closed`, `handled`

### Leaderboard System
- **Role Hierarchy**: owner, co-owner, admin, staff, trial
- **Custom Formatting**: Beautiful embeds with custom emojis
- **Weekly Reset**: Automatic Sunday 4 AM EST weekly stats reset
- **Auto-posting**: Leaderboards posted every Sunday 4 AM EST

### Stats Tracking
- All-time handled/closed tickets
- Weekly handled/closed tickets
- Custom profile messages
- Role assignment dates
- Profile images with Discord banner/avatar

## Setup

1. **Install Dependencies**:
   Dependencies are already installed via the Replit environment.

2. **Set Discord Token**:
   The bot token will be requested when you run the bot.

3. **Configure Server**:
   - Run `.sendticket` in your ticket channel (owner only)
   - Run `.setarchive #channel` to set archive channel
   - Run `.setleaderboard #channel` to set leaderboard channel
   - Run `.ticketlimit <number>` to set ticket limits

4. **Add Staff to Leaderboard**:
   - Use `.lb add @user owner` to add users to roles
   - Valid roles: owner, co-owner, admin, staff, trial

## Permissions

### Owner Only
- `.sendticket`
- `.ticketlimit`
- `.setarchive`
- `.setleaderboard`

### Admin/Mod Only
- `.close`
- `.claim force` / `.unclaim force`
- `.modify`
- `.lb add` / `.lb remove`

### Staff
- `.claim` / `.unclaim`
- `.fm`
- `.add` / `.remove`
- `.rename`
- `.profile edit`
- `.stats`
- `.lb` commands (view only)

## Database

The bot uses SQLite for persistent storage:
- Ticket data and transcripts
# Discord Ticket & Stats Bot

A comprehensive Discord bot for managing tickets, tracking staff statistics, and displaying leaderboards.

## Features

### Ticket System
- **Category Selection**: Create tickets via dropdown (Middleman, Pilot, Verify, Giveaway, Other)
- **Automatic Numbering**: Sequential ticket numbers for organization
- **Ticket Limits**: Set maximum open tickets with `.ticketlimit`
- **Claim/Unclaim System**: Staff can claim tickets for credit tracking
- **Close with Transcripts**: Archive tickets with full transcripts and DM to opener
- **Archive Channel**: Automatic transcript posting with embed summaries

### Staff Commands
- `.sendticket` - Post persistent ticket creation message (owner only)
- `.ticketlimit <number>` - Set maximum open tickets (owner only)
- `.setarchive #channel` - Set archive channel for transcripts (owner only)
- `.setleaderboard #channel` - Set channel for weekly leaderboard posts (owner only)
- `.claim` / `.claim force` - Claim a ticket
- `.unclaim` / `.unclaim force` - Unclaim a ticket
- `.close <reason>` - Close ticket with reason and transcript
- `.fm` - Jump to first message in thread/channel
- `.add @user` - Add user to thread
- `.remove @user` - Remove user from thread
- `.rename <name>` - Rename thread
- `.profile edit <message>` - Set custom profile message
- `.stats [@user]` - View user statistics with profile image
- `.lb` - View all-time leaderboard (handles)
- `.lb w` - View weekly leaderboard (handles)
- `.lb c` - View all-time closes leaderboard
- `.lb cw` - View weekly closes leaderboard
- `.lb add @user <role>` - Add user to leaderboard role
- `.lb remove @user <role>` - Remove user from leaderboard role
- `.modify @user <stat> <value>` - Modify user statistics
  - Stats: `wclosed`, `whandled`, `closed`, `handled`

### Leaderboard System
- **Role Hierarchy**: owner, co-owner, admin, staff, trial
- **Custom Formatting**: Beautiful embeds with custom emojis
- **Weekly Reset**: Automatic Sunday 4 AM EST weekly stats reset
- **Auto-posting**: Leaderboards posted every Sunday 4 AM EST

### Stats Tracking
- All-time handled/closed tickets
- Weekly handled/closed tickets
- Custom profile messages
- Role assignment dates
- Profile images with Discord banner/avatar

## Setup

1. **Install Dependencies**:
   Dependencies are already installed via the Replit environment.

2. **Set Discord Token**:
   The bot token will be requested when you run the bot.

3. **Configure Server**:
   - Run `.sendticket` in your ticket channel (owner only)
   - Run `.setarchive #channel` to set archive channel
   - Run `.setleaderboard #channel` to set leaderboard channel
   - Run `.ticketlimit <number>` to set ticket limits

4. **Add Staff to Leaderboard**:
   - Use `.lb add @user owner` to add users to roles
   - Valid roles: owner, co-owner, admin, staff, trial

## Permissions

### Owner Only
- `.sendticket`
- `.ticketlimit`
- `.setarchive`
- `.setleaderboard`

### Admin/Mod Only
- `.close`
- `.claim force` / `.unclaim force`
- `.modify`
- `.lb add` / `.lb remove`

### Staff
- `.claim` / `.unclaim`
- `.fm`
- `.add` / `.remove`
- `.rename`
- `.profile edit`
- `.stats`
- `.lb` commands (view only)

## Database

The bot uses SQLite for persistent storage:
- Ticket data and transcripts
- User statistics (all-time and weekly)
- Leaderboard role assignments
- Server configuration

Weekly stats automatically reset every Sunday at 4 AM EST.
