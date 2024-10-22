import sqlite3

class BoothSQLite():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_accounts (
                session_cookie TEXT UNIQUE,
                discord_user_id INTEGER PRIMARY KEY,
                discord_channel_id INTEGER
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_items (
                booth_order_number INTEGER PRIMARY KEY,
                booth_item_name TEXT,
                booth_check_only TEXT,
                intent_encoding TEXT,
                download_number_show BOOLEAN,
                changelog_show BOOLEAN,
                archive_this BOOLEAN,
                discord_user_id INTEGER,
                FOREIGN KEY(discord_user_id) REFERENCES booth_accounts(discord_user_id)
            )
        ''')

    def __del__(self):
        self.conn.close()

    def get_booth_items(self):
        self.cursor.execute('''
            SELECT items.booth_order_number,
                            items.booth_item_name,
                            items.booth_check_only,
                            items.intent_encoding,
                            items.download_number_show,
                            items.changelog_show,
                            items.archive_this,
                            accounts.session_cookie,
                            accounts.discord_user_id,
                            accounts.discord_channel_id
            FROM booth_items items
            INNER JOIN booth_accounts accounts
            ON items.discord_user_id = accounts.discord_user_id
        ''')
        return self.cursor.fetchall()

    def get_booth_account(self, discord_user_id):
        self.cursor.execute('''
            SELECT * FROM booth_accounts
            WHERE discord_user_id = ?
        ''', (discord_user_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        return None
    
    def add_booth_account(self, session_cookie, discord_user_id, discord_channel_id):
        self.cursor.execute('''
            INSERT OR REPLACE INTO booth_accounts (session_cookie, discord_user_id, discord_channel_id)
            VALUES (?, ?, ?)
        ''', (session_cookie, discord_user_id, discord_channel_id))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_booth_item(self, discord_user_id, booth_order_number, booth_item_name, booth_check_only, intent_encoding, download_number_show, changelog_show, archive_this):
        booth_account = self.get_booth_account(discord_user_id)
        if booth_account:
            self.cursor.execute('''
                INSERT INTO booth_items (booth_order_number, booth_item_name, booth_check_only, intent_encoding, download_number_show, changelog_show, archive_this, discord_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (booth_order_number,
                  booth_item_name,
                  booth_check_only,
                  intent_encoding,
                  int(download_number_show),
                  int(changelog_show),
                  int(archive_this),
                  discord_user_id))
            self.conn.commit()
            return self.cursor.lastrowid
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")
