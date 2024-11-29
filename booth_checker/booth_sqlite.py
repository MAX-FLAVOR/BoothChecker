import sqlite3

class BoothSQLite():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.cursor = self.conn.cursor()

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
                            items.gift_item,
                            accounts.session_cookie,
                            accounts.discord_user_id,
                            accounts.discord_channel_id
            FROM booth_items items
            INNER JOIN booth_accounts accounts
            ON items.discord_user_id = accounts.discord_user_id
        ''')
        return self.cursor.fetchall()
