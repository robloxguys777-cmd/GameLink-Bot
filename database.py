import sqlite3
import os

DB_PATH = "gamelink.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Guild settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        game_type TEXT,
        verify_role_id INTEGER,
        setup_completed BOOLEAN DEFAULT 0
    )
    ''')
    
    # User verification table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_verifications (
        discord_id INTEGER,
        game_type TEXT,
        game_username TEXT,
        game_id TEXT,
        PRIMARY KEY (discord_id, game_type)
    )
    ''')
    
    # Pending verifications for emoji method
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_verifications (
        discord_id INTEGER PRIMARY KEY,
        roblox_username TEXT,
        roblox_id TEXT,
        required_emojis TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_guild_settings(guild_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT game_type, verify_role_id, setup_completed FROM guild_settings WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_guild_settings(guild_id, game_type, verify_role_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO guild_settings (guild_id, game_type, verify_role_id, setup_completed)
    VALUES (?, ?, ?, 1)
    ON CONFLICT(guild_id) DO UPDATE SET
        game_type = excluded.game_type,
        verify_role_id = excluded.verify_role_id,
        setup_completed = 1
    ''', (guild_id, game_type, verify_role_id))
    conn.commit()
    conn.close()

def link_user(discord_id, game_type, game_username, game_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO user_verifications (discord_id, game_type, game_username, game_id)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(discord_id, game_type) DO UPDATE SET
        game_username = excluded.game_username,
        game_id = excluded.game_id
    ''', (discord_id, game_type, game_username, game_id))
    conn.commit()
    conn.close()

def get_user_by_discord(discord_id, game_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT game_username, game_id FROM user_verifications WHERE discord_id = ? AND game_type = ?", (discord_id, game_type))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_by_game(game_username, game_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id FROM user_verifications WHERE game_username = ? AND game_type = ?", (game_username, game_type))
    row = cursor.fetchone()
    conn.close()
    return row

def save_pending(discord_id, roblox_username, roblox_id, emojis):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO pending_verifications (discord_id, roblox_username, roblox_id, required_emojis)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(discord_id) DO UPDATE SET
        roblox_username = excluded.roblox_username,
        roblox_id = excluded.roblox_id,
        required_emojis = excluded.required_emojis
    ''', (discord_id, roblox_username, roblox_id, emojis))
    conn.commit()
    conn.close()

def get_pending(discord_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT roblox_username, roblox_id, required_emojis FROM pending_verifications WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_pending(discord_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_verifications WHERE discord_id = ?", (discord_id,))
    conn.commit()
    conn.close()
