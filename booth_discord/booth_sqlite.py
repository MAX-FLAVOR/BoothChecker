import sqlite3

class BoothSQLite():
    def __init__(self, db, logger):
        self.logger = logger
        self.conn = sqlite3.connect(db)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_accounts (
                session_cookie TEXT UNIQUE,
                discord_user_id INTEGER PRIMARY KEY
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS booth_items (
                booth_order_number TEXT PRIMARY KEY,
                booth_item_number TEXT,
                discord_user_id INTEGER,
                item_name TEXT,
                intent_encoding TEXT,
                download_number_show BOOLEAN,
                changelog_show BOOLEAN,
                archive_this BOOLEAN,
                gift_item BOOLEAN,
                summary_this BOOLEAN,
                fbx_only BOOLEAN,
                FOREIGN KEY(discord_user_id) REFERENCES booth_accounts(discord_user_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS discord_noti_channels (
                discord_channel_id INTEGER,
                booth_order_number TEXT,
                UNIQUE(discord_channel_id, booth_order_number),         
                FOREIGN KEY(booth_order_number) REFERENCES booth_items(booth_order_number)
            )
        ''')

    def __del__(self):
        self.conn.close()
    
    def add_booth_account(self, session_cookie, discord_user_id):
        self.cursor.execute('''
            SELECT discord_user_id FROM booth_accounts
            WHERE session_cookie = ?
        ''', (session_cookie,))
        owner = self.cursor.fetchone()
        if owner and owner[0] != discord_user_id:
            raise Exception("이미 다른 Discord 계정에 등록된 쿠키입니다.")

        existing_account = self.get_booth_account(discord_user_id)
        if existing_account:
            self.cursor.execute('''
                UPDATE booth_accounts
                SET session_cookie = ?
                WHERE discord_user_id = ?
            ''', (session_cookie, discord_user_id))
        else:
            self.cursor.execute('''
                INSERT INTO booth_accounts (session_cookie, discord_user_id)
                VALUES (?, ?)
            ''', (session_cookie, discord_user_id))
        self.conn.commit()
        return self.get_booth_account(discord_user_id)
    
    def add_booth_item(self, discord_user_id, discord_channel_id, booth_item_number, item_name, intent_encoding,summary_this, fbx_only):
        # Moved import to be local to avoid dependency issues in booth_checker
        from booth import get_booth_order_info

        booth_account = self.get_booth_account(discord_user_id)
        if self.is_item_duplicate(booth_item_number, discord_user_id):
            raise Exception("이미 등록된 아이템입니다.")
        # 서버에 부스 아이템 파일이 남지않도록 하드코딩
        # download_number_show True, changelog_show True, archive_this False
        if booth_account:
            booth_order_info = get_booth_order_info(booth_item_number, ("_plaza_session_nktz7u", booth_account[0]))
            try:
                self.cursor.execute('''
                    INSERT INTO booth_items (
                                    booth_order_number,
                                    booth_item_number,
                                    discord_user_id,
                                    item_name,
                                    intent_encoding,
                                    download_number_show,
                                    changelog_show,
                                    archive_this,
                                    gift_item,
                                    summary_this,
                                    fbx_only
                                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (booth_order_info[1],
                      booth_item_number,
                      discord_user_id,
                      item_name,
                      intent_encoding,
                      True,
                      True,
                      False,
                      booth_order_info[0],
                      summary_this,
                      fbx_only))
                self.add_discord_noti_channel(discord_channel_id, booth_order_info[1])
                self.conn.commit()
            except sqlite3.IntegrityError as exc:
                self.conn.rollback()
                raise Exception("아이템 등록 중 충돌이 발생했습니다.") from exc
            return booth_order_info[1]
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

    def del_booth_account(self, discord_user_id):
        try:
            self.cursor.execute('''
                SELECT EXISTS (
                    SELECT 1 
                    FROM booth_items 
                    WHERE discord_user_id = ?
                );
            ''', (discord_user_id,))
            result = self.cursor.fetchone()
            if result[0] == 1:
                raise Exception("BOOTH 아이템이 등록되어 있습니다. 먼저 아이템을 삭제해주세요.")
            self.cursor.execute('''
                DELETE FROM booth_accounts WHERE discord_user_id = ?
            ''', (discord_user_id,))
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            raise Exception(e)
    
    def del_booth_item(self, discord_user_id, booth_item_number):
        booth_account = self.get_booth_account(discord_user_id)
        if booth_account:
            try:
                # 1. 삭제할 행의 booth_order_number를 먼저 조회합니다.
                self.cursor.execute('''
                    SELECT booth_order_number FROM booth_items 
                    WHERE booth_item_number = ? AND discord_user_id = ?
                ''', (booth_item_number, discord_user_id))
                result = self.cursor.fetchone()
                if not result:
                    raise Exception(f"Item {booth_item_number} not found for user {discord_user_id}")
                
                booth_order_number = result[0]
                self.logger.debug(f"booth_order_number: {booth_order_number}")

                # 2. booth_items 테이블에서 해당 행을 삭제합니다.
                self.cursor.execute('''
                    DELETE FROM booth_items 
                    WHERE booth_item_number = ? AND discord_user_id = ?
                ''', (booth_item_number, discord_user_id))
                deleted_items = self.cursor.rowcount
                
                # 3. 조회된 booth_order_number를 사용하여 discord_noti_channels 테이블에서도 삭제합니다.
                deleted_channels = self.del_discord_noti_channel(booth_order_number)
                self.conn.commit()
                return {'items_deleted': deleted_items, 'channels_deleted': deleted_channels}
            except Exception as e:
                self.conn.rollback()
                raise Exception(e)
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")
        
    def get_booth_account(self, discord_user_id):
        self.cursor.execute('''
            SELECT * FROM booth_accounts
            WHERE discord_user_id = ?
        ''', (discord_user_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        return None

    def is_item_duplicate(self, booth_item_number, discord_user_id):
        self.cursor.execute('''
            SELECT * FROM booth_items
            WHERE booth_item_number = ? AND discord_user_id = ?
        ''', (booth_item_number, discord_user_id))
        result = self.cursor.fetchone()
        return bool(result)
    
    def list_booth_items(self, discord_user_id, discord_channel_id):
        booth_account = self.get_booth_account(discord_user_id)
        if booth_account:
            self.cursor.execute('''
                SELECT bi.booth_item_number 
                FROM booth_items bi
                JOIN discord_noti_channels dnc 
                ON bi.booth_order_number = dnc.booth_order_number
                WHERE bi.discord_user_id = ? 
                AND dnc.discord_channel_id = ?;
            ''', (discord_user_id, discord_channel_id))
            return self.cursor.fetchall()
        else:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

    def add_discord_noti_channel(self, discord_channel_id, booth_order_number):
        self.cursor.execute('''
            SELECT 1 FROM discord_noti_channels
            WHERE discord_channel_id = ? AND booth_order_number = ?
        ''', (discord_channel_id, booth_order_number))
        if self.cursor.fetchone():
            return False

        self.cursor.execute('''
            INSERT INTO discord_noti_channels (discord_channel_id, booth_order_number)
            VALUES (?, ?)
        ''', (discord_channel_id, booth_order_number))
        return True

    def del_discord_noti_channel(self, booth_order_number):
        self.logger.debug(f"del_discord_noti_channel - booth_order_number : {booth_order_number}") # 추가된 로그
        self.cursor.execute('''
            DELETE FROM discord_noti_channels WHERE booth_order_number = ?
        ''', (booth_order_number,))
        return self.cursor.rowcount

    def update_discord_noti_channel(self, discord_user_id, discord_channel_id, booth_item_number):
        booth_order_number = self.get_booth_order_number(booth_item_number, discord_user_id)
        if not booth_order_number:
            raise Exception("Item not found")
        self.cursor.execute('''
            UPDATE discord_noti_channels
            SET discord_channel_id = ?
            WHERE booth_order_number = ?
        ''', (discord_channel_id, booth_order_number))
        self.conn.commit()
        return self.cursor.rowcount

    def get_booth_order_number(self, booth_item_number, discord_user_id):
        self.cursor.execute('''
            SELECT booth_order_number FROM booth_items
            WHERE booth_item_number = ? AND discord_user_id = ?
        ''', (booth_item_number, discord_user_id))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_booth_item_count(self, discord_user_id):
        self.cursor.execute('SELECT COUNT(*) FROM booth_items WHERE discord_user_id = ?', (discord_user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
