import sqlite3

class BoothSQLite():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.execute("PRAGMA journal_mode=WAL;")
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
    
    def add_booth_item(self, discord_user_id, booth_order_number, booth_item_name, booth_check_only, intent_encoding):
        booth_account = self.get_booth_account(discord_user_id)
        # 서버에 부스 아이템 파일이 남지않도록 하드코딩
        # download_number_show False, changelog_show True, archive_this False
        if booth_account:
            self.cursor.execute('''
                INSERT OR REPLACE INTO booth_items (booth_order_number, booth_item_name, booth_check_only, intent_encoding, download_number_show, changelog_show, archive_this, discord_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (booth_order_number,
                  booth_item_name,
                  booth_check_only,
                  intent_encoding,
                  False,
                  True,
                  False,
                  discord_user_id))
            self.conn.commit()
            return self.cursor.lastrowid
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

    def remove_booth_account(self, discord_user_id):
        try:
            self.cursor.execute('''
                DELETE FROM booth_accounts WHERE discord_user_id = ?
            ''', (discord_user_id,))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            raise Exception(f'BOOTH 계정 삭제 실패: {e}')
    
    def remove_booth_item(self, discord_user_id, booth_order_number):
        booth_account = self.get_booth_account(discord_user_id)
        if booth_account:
            try:
                self.cursor.execute('''
                    DELETE FROM booth_items WHERE booth_order_number = ? AND discord_user_id = ?
                ''', (int(booth_order_number), discord_user_id))
                self.conn.commit()
                return self.cursor.lastrowid
            except Exception as e:
                raise Exception(f'BOOTH 아이템 삭제 실패: {e}')
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")
    
    def list_booth_items(self, discord_user_id):
        booth_account = self.get_booth_account(discord_user_id)
        if booth_account:
            self.cursor.execute('''
                SELECT booth_order_number FROM booth_items WHERE discord_user_id = ?
            ''', (discord_user_id,))
            return self.cursor.fetchall()
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")