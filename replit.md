# Overview

This is a Discord ticket management and staff statistics bot built with discord.py. The bot provides a comprehensive ticket system with category-based creation, claim/unclaim functionality, transcript archiving, and automated staff performance tracking. It features a hierarchical leaderboard system that resets weekly and displays staff statistics with custom profile images.

**Status**: ✅ Bot is fully implemented and running as "kirei#2389"

# Recent Changes

**October 17, 2025** (Latest Update)
- Added .setstaffroles command for configurable staff permissions
- Updated all commands to use silent permission checks (no error messages)
- Redesigned stats embed with new 3x2 layout (Rank/Closed/Handled stats)
- Enhanced stats image: centered username, Discord join date, bigger pfp (200x200), proportional background
- Updated ticket creation to ping role and show type as heading
- Made .rename command silent (no confirmation)
- Updated .claim to send embed reply and delete original message
- Changed leaderboard formatting to bold text headings
- Added database migration for existing deployments
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
  - `server_config`: Guild-specific settings including ticket limits, archive channels, and leaderboard channels

## Ticket System Architecture
- **Persistent UI Components**: Dropdown select menu (TicketCategorySelect) for ticket creation with 5 categories (middleman, pilot, verify, giveaway, other)
- **Ticket Lifecycle**:
  1. Creation via category selection
  2. Optional claim by staff (with force claim for admins)
  3. Closure with reason and confirmation
  4. Transcript generation and archiving
  5. DM notification to ticket opener
- **Limit Enforcement**: Configurable maximum open tickets with ephemeral error messages when full
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
- **Avatar Overlay**: Circular masked avatar positioned on left side
- **Async Image Fetching**: Uses aiohttp for non-blocking image downloads

## Permission Structure
- **Owner-only**: `.sendticket`, `.ticketlimit`, server configuration commands
- **Admin/Mod**: `.claim force`, `.unclaim force`, `.modify`, `.close`
- **Staff**: `.claim`, `.unclaim`, `.add`, `.remove`, `.rename`, `.profile edit`, `.stats`, `.lb` commands
- **Role-based Access**: Leaderboard management (`.lb add`/`.lb remove`) restricted to admins

## Transcript System
- **Archive Channel**: Dedicated channel for permanent transcript storage
- **Embed Format**: f9e6f0 color throughout, includes opener, handler, closer, timestamps, duration, and close reason
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