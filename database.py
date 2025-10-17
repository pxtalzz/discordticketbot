import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Tuple

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER UNIQUE,
                    category TEXT,
                    opener_id INTEGER,
                    handler_id INTEGER,
                    closer_id INTEGER,
                    created_at TEXT,
                    closed_at TEXT,
                    close_reason TEXT,
                    status TEXT DEFAULT 'open'
                )
            ''')
            
            async with db.execute("PRAGMA table_info(server_config)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                if 'staff_role_ids' not in column_names and column_names:
                    await db.execute('ALTER TABLE server_config ADD COLUMN staff_role_ids TEXT')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    all_time_handled INTEGER DEFAULT 0,
                    all_time_closed INTEGER DEFAULT 0,
                    weekly_handled INTEGER DEFAULT 0,
                    weekly_closed INTEGER DEFAULT 0,
                    profile_message TEXT,
                    role_assignment_date TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS leaderboard_roles (
                    user_id INTEGER,
                    role_name TEXT,
                    PRIMARY KEY (user_id, role_name)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_config (
                    guild_id INTEGER PRIMARY KEY,
                    ticket_limit INTEGER DEFAULT 0,
                    archive_channel_id INTEGER,
                    ticket_message_id INTEGER,
                    ticket_channel_id INTEGER,
                    leaderboard_channel_id INTEGER,
                    staff_role_ids TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS weekly_reset (
                    id INTEGER PRIMARY KEY,
                    last_reset TEXT
                )
            ''')
            
            await db.commit()
    
    async def get_ticket_limit(self, guild_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT ticket_limit FROM server_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def set_ticket_limit(self, guild_id: int, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_config (guild_id, ticket_limit) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET ticket_limit = ?
            ''', (guild_id, limit, limit))
            await db.commit()
    
    async def get_open_ticket_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM tickets WHERE status = 'open'"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def create_ticket(self, channel_id: int, category: str, opener_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO tickets (channel_id, category, opener_id, created_at, status)
                VALUES (?, ?, ?, ?, 'open')
            ''', (channel_id, category, opener_id, datetime.utcnow().isoformat()))
            await db.commit()
            return cursor.lastrowid
    
    async def claim_ticket(self, channel_id: int, handler_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tickets SET handler_id = ? WHERE channel_id = ?
            ''', (handler_id, channel_id))
            await db.commit()
            
            await db.execute('''
                INSERT INTO user_stats (user_id, all_time_handled, weekly_handled)
                VALUES (?, 1, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    all_time_handled = all_time_handled + 1,
                    weekly_handled = weekly_handled + 1
            ''', (handler_id,))
            await db.commit()
    
    async def unclaim_ticket(self, channel_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT handler_id FROM tickets WHERE channel_id = ?',
                (channel_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    handler_id = result[0]
                    await db.execute('''
                        UPDATE user_stats SET
                            all_time_handled = all_time_handled - 1,
                            weekly_handled = weekly_handled - 1
                        WHERE user_id = ?
                    ''', (handler_id,))
                    
            await db.execute('''
                UPDATE tickets SET handler_id = NULL WHERE channel_id = ?
            ''', (channel_id,))
            await db.commit()
    
    async def close_ticket(self, channel_id: int, closer_id: int, reason: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tickets SET 
                    closer_id = ?,
                    close_reason = ?,
                    closed_at = ?,
                    status = 'closed'
                WHERE channel_id = ?
            ''', (closer_id, reason, datetime.utcnow().isoformat(), channel_id))
            await db.commit()
            
            await db.execute('''
                INSERT INTO user_stats (user_id, all_time_closed, weekly_closed)
                VALUES (?, 1, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    all_time_closed = all_time_closed + 1,
                    weekly_closed = weekly_closed + 1
            ''', (closer_id,))
            await db.commit()
    
    async def get_ticket_info(self, channel_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM tickets WHERE channel_id = ?',
                (channel_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {
                        'ticket_number': result[0],
                        'channel_id': result[1],
                        'category': result[2],
                        'opener_id': result[3],
                        'handler_id': result[4],
                        'closer_id': result[5],
                        'created_at': result[6],
                        'closed_at': result[7],
                        'close_reason': result[8],
                        'status': result[9]
                    }
                return None
    
    async def get_user_stats(self, user_id: int) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM user_stats WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {
                        'user_id': result[0],
                        'all_time_handled': result[1],
                        'all_time_closed': result[2],
                        'weekly_handled': result[3],
                        'weekly_closed': result[4],
                        'profile_message': result[5],
                        'role_assignment_date': result[6]
                    }
                return {
                    'user_id': user_id,
                    'all_time_handled': 0,
                    'all_time_closed': 0,
                    'weekly_handled': 0,
                    'weekly_closed': 0,
                    'profile_message': None,
                    'role_assignment_date': None
                }
    
    async def update_profile_message(self, user_id: int, message: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO user_stats (user_id, profile_message)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET profile_message = ?
            ''', (user_id, message, message))
            await db.commit()
    
    async def modify_stats(self, user_id: int, stat_type: str, value: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f'''
                INSERT INTO user_stats (user_id, {stat_type})
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET {stat_type} = {stat_type} + ?
            ''', (user_id, value, value))
            await db.commit()
    
    async def add_leaderboard_role(self, user_id: int, role_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR IGNORE INTO leaderboard_roles (user_id, role_name)
                VALUES (?, ?)
            ''', (user_id, role_name))
            await db.commit()
    
    async def remove_leaderboard_role(self, user_id: int, role_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM leaderboard_roles WHERE user_id = ? AND role_name = ?
            ''', (user_id, role_name))
            await db.commit()
    
    async def get_user_leaderboard_role(self, user_id: int) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT role_name FROM leaderboard_roles WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def get_leaderboard_data(self, stat_type: str = 'all_time') -> List[Tuple]:
        if stat_type == 'all_time':
            stat_col = 'all_time_handled + all_time_closed'
        elif stat_type == 'weekly':
            stat_col = 'weekly_handled + weekly_closed'
        elif stat_type == 'all_time_closed':
            stat_col = 'all_time_closed'
        elif stat_type == 'weekly_closed':
            stat_col = 'weekly_closed'
        else:
            stat_col = 'all_time_handled + all_time_closed'
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(f'''
                SELECT user_id, all_time_handled, all_time_closed, 
                       weekly_handled, weekly_closed
                FROM user_stats
                WHERE {stat_col} > 0
                ORDER BY {stat_col} DESC
            ''') as cursor:
                return await cursor.fetchall()
    
    async def reset_weekly_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE user_stats SET weekly_handled = 0, weekly_closed = 0
            ''')
            await db.execute('''
                INSERT OR REPLACE INTO weekly_reset (id, last_reset)
                VALUES (1, ?)
            ''', (datetime.utcnow().isoformat(),))
            await db.commit()
    
    async def set_archive_channel(self, guild_id: int, channel_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_config (guild_id, archive_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET archive_channel_id = ?
            ''', (guild_id, channel_id, channel_id))
            await db.commit()
    
    async def get_archive_channel(self, guild_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT archive_channel_id FROM server_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def set_ticket_message(self, guild_id: int, message_id: int, channel_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_config (guild_id, ticket_message_id, ticket_channel_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 
                    ticket_message_id = ?,
                    ticket_channel_id = ?
            ''', (guild_id, message_id, channel_id, message_id, channel_id))
            await db.commit()
    
    async def set_leaderboard_channel(self, guild_id: int, channel_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_config (guild_id, leaderboard_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET leaderboard_channel_id = ?
            ''', (guild_id, channel_id, channel_id))
            await db.commit()
    
    async def get_leaderboard_channel(self, guild_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT leaderboard_channel_id FROM server_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def execute_raw(self, query: str, params: tuple = ()):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()
    
    async def set_staff_roles(self, guild_id: int, role_ids: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_config (guild_id, staff_role_ids)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET staff_role_ids = ?
            ''', (guild_id, role_ids, role_ids))
            await db.commit()
    
    async def get_staff_roles(self, guild_id: int) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT staff_role_ids FROM server_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return [int(rid) for rid in result[0].split(',')]
                return []
