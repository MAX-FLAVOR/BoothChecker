import sqlite3

class BoothSQLite():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_accounts (
                session_cookie TEXT UNIQUE,
                discord_user_id TEXT PRIMARY KEY,
                discord_channel_id TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_items (
                session_cookie TEXT,
                discord_channel_id TEXT,
                booth_order_number TEXT PRIMARY KEY,
                booth_item_name TEXT,
                booth_check_only TEXT,
                intent_encoding TEXT,
                download_number_show BOOLEAN,
                changelog_show BOOLEAN,
                archive_this BOOLEAN,
                FOREIGN KEY(session_cookie, discord_channel_id) REFERENCES booth_accounts(session_cookie, discord_channel_id)
            )
        ''')

    def __del__(self):
        self.conn.close()

    def get_booth_items(self):
        self.cursor.execute('''
            SELECT * FROM booth_items
        ''')
        return self.cursor.fetchall()

    def get_booth_accounts(self, discord_user_id):
        self.cursor.execute('''
            SELECT session_cookie, discord_channel_id FROM booth_accounts
            WHERE discord_user_id = ?
        ''', (discord_user_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        return None
    
    def add_booth_accounts(self, session_cookie, discord_user_id, discord_channel_id):
        self.cursor.execute('''
            INSERT OR REPLACE INTO session_cookies (session_cookie, discord_user_id, discord_channel_id)
            VALUES (?, ?, ?)
        ''', (session_cookie, discord_user_id, discord_channel_id))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_item(self, discord_user_id, booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this):
        booth_account = self.get_booth_accounts(discord_user_id)
        if booth_account:
            self.cursor.execute('''
                INSERT INTO items (session_cookie, discord_channel_id, booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (booth_account[0], booth_account[1], booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this))
            self.conn.commit()
            return self.cursor.lastrowid
