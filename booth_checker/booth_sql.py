import logging
import time
import psycopg


logger = logging.getLogger('BoothChecker')


class BoothPostgres:
    def __init__(self, conn_params, retries=5, delay=2):
        self.conn = self._connect_with_retry(conn_params, retries, delay)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def __del__(self):
        try:
            self.cursor.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass

    def get_booth_items(self):
        self.cursor.execute('''
            SELECT  items.booth_order_number,
                    items.booth_item_number,
                    items.item_name,
                    items.intent_encoding,
                    items.download_number_show,
                    items.changelog_show,
                    items.archive_this,
                    items.gift_item,
                    items.summary_this,
                    items.fbx_only,
                    accounts.session_cookie,
                    accounts.discord_user_id,
                    channels.discord_channel_id
            FROM booth_items items
            INNER JOIN booth_accounts accounts
                ON items.discord_user_id = accounts.discord_user_id
            INNER JOIN discord_noti_channels channels
                ON items.booth_order_number = channels.booth_order_number
        ''')
        return self.cursor.fetchall()

    def _connect_with_retry(self, conn_params, retries=5, delay=2):
        for attempt in range(1, retries + 1):
            try:
                return psycopg.connect(**conn_params)
            except psycopg.OperationalError as exc:
                if attempt == retries:
                    logger.error("PostgreSQL 연결에 실패했습니다. 설정을 확인해주세요.")
                    raise
                logger.warning(
                    "PostgreSQL 연결 재시도 %s/%s: %s",
                    attempt,
                    retries,
                    exc,
                )
                time.sleep(delay)
