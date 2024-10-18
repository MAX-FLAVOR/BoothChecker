import sqlite3

class BoothSQLite():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_cookies (
                session_cookie TEXT,
                discord_user_id TEXT PRIMARY KEY
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                session_cookie TEXT,
                booth_order_number TEXT PRIMARY KEY,
                booth_item_name TEXT,
                booth_check_only TEXT,
                intent_encoding TEXT,
                download_number_show BOOLEAN,
                changelog_show BOOLEAN,
                archive_this BOOLEAN,
                FOREIGN KEY(session_cookie) REFERENCES session_cookies(session_cookie)
            )
        ''')

    def __del__(self):
        self.conn.close()

    def get_items(self):
        self.cursor.execute('''
            SELECT * FROM items
        ''')
        return self.cursor.fetchall()
    
    def get_check_only(self, booth_order_number):
        self.cursor.execute('''
            SELECT * FROM booth_check_only WHERE item_id = ?
        ''', (booth_order_number,))
        return self.cursor.fetchall()

    def get_session_cookie_by_discord_user_id(self, discord_user_id):
        self.cursor.execute('''
            SELECT session_cookie FROM session_cookies
            WHERE discord_user_id = ?
        ''', (discord_user_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None
    
    def add_session_cookie(self, session_cookie, discord_user_id):
        self.cursor.execute('''
            INSERT INTO session_cookies (session_cookie, discord_user_id)
            VALUES (?, ?)
        ''', (session_cookie, discord_user_id))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_item(self, discord_user_id, booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this):
        session_cookie = self.get_session_cookie_by_discord_user_id(discord_user_id)
        if session_cookie:
            self.cursor.execute('''
                INSERT INTO items (session_cookie, booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_cookie, booth_order_number, booth_item_name, intent_encoding, download_number_show, changelog_show, archive_this))
            self.conn.commit()
            return self.cursor.lastrowid
