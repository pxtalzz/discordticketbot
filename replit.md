# Overview

This is a Discord ticket management and staff statistics bot built with discord.py. The bot provides a comprehensive ticket system with category-based creation, claim/unclaim functionality, transcript archiving, and automated staff performance tracking. It features a hierarchical leaderboard system that resets weekly and displays staff statistics with custom profile images.

**Status**: ✅ Bot is fully implemented and running as "kirei#2389"

# Recent Changes

**November 22, 2025** (Latest Update - Staff Role Tracking & Code Fixes)
- Added automatic tracking of staff role assignment dates via on_member_update event listener
- Stats command join date now shows when user received staff role (ID: 1407881544202195004)
- Added database function to store role assignment timestamps in ISO-8601 UTC format
- Updated unclaim command to show embed message with color #c5bdff and delete command message
- Fixed all deprecated datetime.utcnow() calls to use datetime.now(timezone.utc) in database.py
- Reorganized project structure by moving files from nested directory to root
- Verified all Python dependencies are properly installed (discord.py, aiohttp, aiosqlite, pillow, python-dotenv, pytz)
- Confirmed bot runs successfully and connects to Discord as "kirei#2270"
- All code modernized to follow Python 3.11+ best practices

**October 19, 2025** (Previous Update - Bug Fixes & UI Improvements v2)
- Fixed "interaction failed" error for ticket creation by adding persistent view registration with custom_id
- Sized up leaderboard titles significantly using Unicode bold characters (𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃)
- Added debug logging to diagnose potential double message issue in .rename, .stats, and .lb commands
- Configured Reserved VM deployment for always-on bot operation
- Fixed .stats command to no longer delete user's command message
- Fixed double messages bug in .stats and .lb commands by removing redundant bot.fetch_user() calls
- Made leaderboard names clickable by using <@{user_id}> format instead of @{user.name}
- Updated ticket close confirmation embed: "Ticket Confirmation" title with "Credit given:" field
- Updated ticket close final embed: "ticket closed <a:Heart:1396388971818520576>" title with proper formatting
- Verified bot runs successfully as "kirei#2389"

**October 17, 2025** (Previous Update - Bug Fixes & Improvements)
- Fixed .stats command to ensure only one message is sent (now deletes command message after sending stats)
- Updated leaderboard role labels to: owner, co-owner, head admin, admin, staff, trial staff
- Enhanced close command confirmation:
  - Shows "Ticket Confirmation" as title with "are you sure you want to close?" subtitle
  - Displays "Credit given: (handler)" field showing who will receive credit
- Added final closing embed:
  - Title: "ticket closed <a:Heart:1396388971818520576>"
  - Shows closer mention and reason in description
- Fixed all type errors and LSP diagnostics:
  - Changed None default parameters to empty strings for type safety
  - Added null checks for ticket_info retrieval
  - Added is_running() checks before starting background tasks
- Verified bot runs successfully as "kirei#2389"

**October 17, 2025** (Previous Update - Major Improvements)
- Changed max tickets message to "TAIYO is currently at max tickets. Please try again later."
- Enhanced stats system:
  - Increased profile picture size from 200x200 to 250x250
  - Increased username font size from 48px to 60px for better visibility
  - Relocated staff join date to bottom right corner with rounded background
  - Join date now displays as Discord timestamp showing when user received role 1407881544202195004
  - Rank now shows highest staff role from hierarchical role list (Owner → Co-Owner → Head Admin → Admin → Mod → Trial Mod → Lead MM → MM → Trial MM → Pilot → Trial Pilot)
- Improved transcript system:
  - Changed transcript file format from .txt to .html with Discord-themed styling
  - Simplified transcript filename to "ticket #X.html"
  - Reformatted transcript embed to show opened by/closed by/handled by on one line
  - Added Discord timestamps for opened at/closed at times
- Updated leaderboard:
  - Changed all leaderboard titles to lowercase ("leaderboard", "closed leaderboard", "weekly leaderboard")
  - .lb add command remains admin-only
- Added .setroles command for configurable role-based permissions (admin, owner, moderator, staff)
- Fixed .setstaffroles database initialization with proper column migration
- Added new database columns for role type management (admin_role_ids, owner_role_ids, moderator_role_ids)
- Verified bot runs successfully as "kirei#2389"

**Previous Updates**
- Added .setstaffroles command for configurable staff permissions
- Updated all commands to use silent permission checks (no error messages)
- Redesigned stats embed with new 3x2 layout (Rank/Closed/Handled stats)
- Updated ticket creation to ping role and show type as heading
- Made .rename command silent (no confirmation)
- Updated .claim to send embed reply and delete original message
- Changed leaderboard formatting to bold text headings
- Implemented complete ticket system with 5 categories (middleman, pilot, verify, giveaway, other)
- Created stats image generation (885x303px) with Discord banner/avatar support
- Implemented automated Sunday 4 AM EST weekly reset and leaderboard posting
- Set up database schema with SQLite for persistent storage
- Added admin commands (.modify, .lb add/remove, .claim force, .unclaim force)

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **discord.py**: Core Discord bot framework with commands extension and app_commands for slash commands
- **Command Prefix**: Dot (`.`) prefix for text-based commands
- **Intents**: Requires message_content, members, and guilds intents for full functionality

## Database Design
- **SQLite with aiosqlite**: Async database operations for non-blocking I/O
- **Schema Structure**:
  - `tickets`: Tracks ticket lifecycle with auto-incrementing ticket numbers, channel associations, handler/closer assignments, and status tracking
  - `user_stats`: Stores all-time and weekly statistics (handled/closed counts), custom profile messages, and role assignment dates
  - `leaderboard_roles`: Many-to-many relationship for user-role assignments in leaderboard hierarchy
  - `server_config`: Guild-specific settings including ticket limits, archive channels, leaderboard channels, and role type configurations (staff_role_ids, admin_role_ids, owner_role_ids, moderator_role_ids)

## Ticket System Architecture
- **Persistent UI Components**: Dropdown select menu (TicketCategorySelect) for ticket creation with 5 categories (middleman, pilot, verify, giveaway, other)
- **Ticket Lifecycle**:
  1. Creation via category selection
  2. Optional claim by staff (with force claim for admins)
  3. Closure with reason and confirmation
  4. Transcript generation and archiving
  5. DM notification to ticket opener
- **Limit Enforcement**: Configurable maximum open tickets with ephemeral message "Max tickets are currently opened, try again later." when full
- **Credit System**: Automatic credit attribution on claim/unclaim actions

## Statistics & Leaderboard System
- **Dual Tracking**: Separate all-time and weekly statistics for both handled and closed tickets
- **Role Hierarchy**: Five-tier system (owner → co-owner → admin → staff → trial) with custom emojis per role
- **Weekly Reset**: Automated Sunday 4 AM EST reset of weekly statistics using discord.py tasks
- **Leaderboard Formatting**: 
  - Custom titles with decorative Unicode characters
  - Role-based sections (hidden if empty)
  - Descending sort within each role tier
  - Support for both handles and closes leaderboards

## Image Generation
- **Stats Profile Cards**: 885x303px images generated with PIL (Pillow)
- **Background Logic**:
  - Primary: Blurred Discord banner if available
  - Fallback: Blurred avatar image
- **Avatar Overlay**: Circular masked avatar (250x250) positioned on left side
- **Username Display**: Centered, 60px bold font, positioned at y=120 for optimal visibility
- **Join Date Badge**: Discord timestamp of staff role assignment displayed in bottom-right with rounded rectangle background
- **Async Image Fetching**: Uses aiohttp for non-blocking image downloads

## Permission Structure
- **Owner-only**: `.sendticket`, `.ticketlimit`, `.setstaffroles`, `.setroles`, server configuration commands
- **Admin/Mod**: `.claim force`, `.unclaim force`, `.modify`, `.close`
- **Staff**: `.claim`, `.unclaim`, `.add`, `.remove`, `.rename`, `.profile edit`, `.stats`, `.lb` commands
- **Role-based Access**: Leaderboard management (`.lb add`/`.lb remove`) restricted to admins
- **Configurable Roles**: Use `.setroles <type> @role1 @role2...` to set admin, owner, moderator, or staff roles

## Transcript System
- **Archive Channel**: Dedicated channel for permanent transcript storage
- **File Format**: HTML files with Discord-themed styling (dark mode colors, message cards)
- **Filename**: Simplified to "ticket #X.html" format
- **Embed Format**: f9e6f0 color with compact layout showing opened by/closed by/handled by on one line, Discord timestamps for dates, and close reason
- **Dual Delivery**: Posted to archive channel and DM'd to ticket opener with button link back to thread
- **Confirmation Prompts**: Two-step confirmation process for ticket closure

## Task Automation
- **Weekly Reset**: discord.py tasks loop for Sunday 4 AM EST execution
- **Auto-posting**: Leaderboards automatically posted to configured channel on weekly reset
- **Timezone Handling**: pytz for EST/EDT timezone conversions

# External Dependencies

## Discord API
- **discord.py**: Main bot framework with commands, app_commands, and UI components
- **Required Intents**: message_content, members, guilds

## Database
- **SQLite**: Local file-based database (`bot_data.db`)
- **aiosqlite**: Async SQLite driver for non-blocking database operations

## Image Processing
- **Pillow (PIL)**: Image generation, manipulation, blurring effects, and circular masking
- **aiohttp**: Async HTTP client for fetching Discord avatars and banners

## Utilities
- **python-dotenv**: Environment variable management for bot token
- **pytz**: Timezone handling for EST scheduling
- **datetime**: Timestamp tracking and duration calculations

## Discord Assets
- **Custom Emojis**: Five role-specific animated/static emojis (IDs hardcoded in ROLE_EMOJIS dict)
- **Embed Color**: Consistent f9e6f0 hex color throughout all embeds

## Configuration
- **Environment Variables**: Bot token stored in `.env` file
- **Guild-specific Settings**: Archive channels, leaderboard channels, and ticket limits stored per-guild in database