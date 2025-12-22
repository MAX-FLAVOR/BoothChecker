import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_int(value):
    if isinstance(value, Decimal):
        return int(value)
    return value


class BoothDynamoDB:
    def __init__(self, config, booth, logger):
        self.logger = logger
        self.booth = booth
        self.config = config
        self.dynamodb = self._connect_with_retry(config)
        self._ensure_tables()
        tables = config['tables']
        self.accounts_table = self.dynamodb.Table(tables['accounts'])
        self.items_table = self.dynamodb.Table(tables['items'])
        self.channels_table = self.dynamodb.Table(tables['channels'])

    def _connect_with_retry(self, config, retries=5, delay=2):
        for attempt in range(1, retries + 1):
            try:
                return boto3.resource(
                    'dynamodb',
                    region_name=config.get('region'),
                    endpoint_url=config.get('endpoint_url'),
                )
            except ClientError as exc:
                if attempt == retries:
                    self.logger.error("DynamoDB 연결에 실패했습니다. 설정을 확인해주세요.")
                    raise
                self.logger.warning(
                    "DynamoDB 연결 재시도 %s/%s: %s",
                    attempt,
                    retries,
                    exc,
                )
                time.sleep(delay)

    def _ensure_tables(self):
        table_names = self.config['tables']
        client = self.dynamodb.meta.client
        existing = set(client.list_tables().get('TableNames', []))

        if table_names['accounts'] not in existing:
            client.create_table(
                TableName=table_names['accounts'],
                AttributeDefinitions=[
                    {'AttributeName': 'discord_user_id', 'AttributeType': 'N'},
                    {'AttributeName': 'session_cookie', 'AttributeType': 'S'},
                ],
                KeySchema=[{'AttributeName': 'discord_user_id', 'KeyType': 'HASH'}],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'session_cookie-index',
                        'KeySchema': [{'AttributeName': 'session_cookie', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                    }
                ],
            )
            client.get_waiter('table_exists').wait(TableName=table_names['accounts'])

        if table_names['items'] not in existing:
            client.create_table(
                TableName=table_names['items'],
                AttributeDefinitions=[
                    {'AttributeName': 'booth_order_number', 'AttributeType': 'S'},
                    {'AttributeName': 'discord_user_id', 'AttributeType': 'N'},
                    {'AttributeName': 'booth_item_number', 'AttributeType': 'S'},
                ],
                KeySchema=[{'AttributeName': 'booth_order_number', 'KeyType': 'HASH'}],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'discord_user_id-booth_item_number-index',
                        'KeySchema': [
                            {'AttributeName': 'discord_user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'booth_item_number', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                    }
                ],
            )
            client.get_waiter('table_exists').wait(TableName=table_names['items'])

        if table_names['channels'] not in existing:
            client.create_table(
                TableName=table_names['channels'],
                AttributeDefinitions=[
                    {'AttributeName': 'booth_order_number', 'AttributeType': 'S'},
                    {'AttributeName': 'discord_channel_id', 'AttributeType': 'N'},
                ],
                KeySchema=[
                    {'AttributeName': 'booth_order_number', 'KeyType': 'HASH'},
                    {'AttributeName': 'discord_channel_id', 'KeyType': 'RANGE'},
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'discord_channel_id-index',
                        'KeySchema': [
                            {'AttributeName': 'discord_channel_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'booth_order_number', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                    }
                ],
            )
            client.get_waiter('table_exists').wait(TableName=table_names['channels'])

    def add_booth_account(self, session_cookie, discord_user_id):
        existing_owner = self._find_account_by_cookie(session_cookie)
        if existing_owner and existing_owner != discord_user_id:
            raise Exception("이미 다른 Discord 계정에 등록된 쿠키입니다.")

        self.accounts_table.put_item(
            Item={
                'discord_user_id': _to_decimal(discord_user_id),
                'session_cookie': session_cookie,
            }
        )
        return self.get_booth_account(discord_user_id)

    def add_booth_item(
        self,
        discord_user_id,
        discord_channel_id,
        booth_item_number,
        booth_order_number,
        item_name,
        intent_encoding,
        summary_this,
        fbx_only,
    ):
        booth_account = self.get_booth_account(discord_user_id)
        if self.is_item_duplicate(booth_item_number, discord_user_id):
            raise Exception("이미 등록된 아이템입니다.")
        if not booth_account:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

        if booth_order_number:
            booth_order_info = (False, booth_order_number)
        else:
            booth_order_info = self.booth.get_booth_order_info(
                booth_item_number,
                ("_plaza_session_nktz7u", booth_account[0]),
            )

        try:
            self.items_table.put_item(
                Item={
                    'booth_order_number': booth_order_info[1],
                    'booth_item_number': booth_item_number,
                    'discord_user_id': _to_decimal(discord_user_id),
                    'item_name': item_name,
                    'intent_encoding': intent_encoding,
                    'download_number_show': True,
                    'changelog_show': True,
                    'archive_this': False,
                    'gift_item': booth_order_info[0],
                    'summary_this': summary_this,
                    'fbx_only': fbx_only,
                },
                ConditionExpression='attribute_not_exists(booth_order_number)',
            )
            self.add_discord_noti_channel(
                discord_channel_id,
                booth_order_info[1],
                use_transaction=False,
            )
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise Exception("아이템 등록 중 충돌이 발생했습니다.") from exc
            raise

        return booth_order_info[1]

    def del_booth_account(self, discord_user_id):
        if self.get_booth_item_count(discord_user_id) > 0:
            raise Exception("BOOTH 아이템이 등록되어 있습니다. 먼저 아이템을 삭제해주세요.")
        response = self.accounts_table.delete_item(
            Key={'discord_user_id': _to_decimal(discord_user_id)},
            ReturnValues='ALL_OLD',
        )
        return 1 if 'Attributes' in response else 0

    def del_booth_item(self, discord_user_id, booth_item_number):
        booth_account = self.get_booth_account(discord_user_id)
        if not booth_account:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

        booth_order_number = self.get_booth_order_number(booth_item_number, discord_user_id)
        if not booth_order_number:
            raise Exception(f"Item {booth_item_number} not found for user {discord_user_id}")

        deleted_channels = self.del_discord_noti_channel(booth_order_number, use_transaction=False)
        response = self.items_table.delete_item(
            Key={'booth_order_number': booth_order_number},
            ReturnValues='ALL_OLD',
        )
        deleted_items = 1 if 'Attributes' in response else 0
        return {'items_deleted': deleted_items, 'channels_deleted': deleted_channels}

    def get_booth_account(self, discord_user_id):
        response = self.accounts_table.get_item(
            Key={'discord_user_id': _to_decimal(discord_user_id)}
        )
        item = response.get('Item')
        if not item:
            return None
        return (item.get('session_cookie'), _to_int(item.get('discord_user_id')))

    def is_item_duplicate(self, booth_item_number, discord_user_id):
        response = self.items_table.query(
            IndexName='discord_user_id-booth_item_number-index',
            KeyConditionExpression=
                Key('discord_user_id').eq(_to_decimal(discord_user_id))
                & Key('booth_item_number').eq(booth_item_number),
        )
        return response.get('Count', 0) > 0

    def list_booth_items(self, discord_user_id, discord_channel_id):
        booth_account = self.get_booth_account(discord_user_id)
        if not booth_account:
            raise Exception("BOOTH 계정이 등록되어 있지 않습니다.")

        response = self.channels_table.query(
            IndexName='discord_channel_id-index',
            KeyConditionExpression=Key('discord_channel_id').eq(_to_decimal(discord_channel_id)),
        )
        booth_order_numbers = [item['booth_order_number'] for item in response.get('Items', [])]
        if not booth_order_numbers:
            return []

        results = []
        for booth_order_number in booth_order_numbers:
            item_response = self.items_table.get_item(Key={'booth_order_number': booth_order_number})
            booth_item = item_response.get('Item')
            if booth_item and _to_int(booth_item.get('discord_user_id')) == discord_user_id:
                results.append((booth_item.get('booth_item_number'),))
        return results

    def add_discord_noti_channel(self, discord_channel_id, booth_order_number, use_transaction=True, cursor=None):
        return self._insert_discord_noti_channel(discord_channel_id, booth_order_number)

    def del_discord_noti_channel(self, booth_order_number, use_transaction=True, cursor=None):
        self.logger.debug("del_discord_noti_channel - booth_order_number : %s", booth_order_number)
        return self._delete_discord_noti_channel(booth_order_number)

    def update_discord_noti_channel(self, discord_user_id, discord_channel_id, booth_item_number):
        booth_order_number = self.get_booth_order_number(booth_item_number, discord_user_id)
        if not booth_order_number:
            raise Exception("Item not found")
        deleted = self._delete_discord_noti_channel(booth_order_number)
        self._insert_discord_noti_channel(discord_channel_id, booth_order_number)
        return max(deleted, 1)

    def get_booth_order_number(self, booth_item_number, discord_user_id):
        response = self.items_table.query(
            IndexName='discord_user_id-booth_item_number-index',
            KeyConditionExpression=
                Key('discord_user_id').eq(_to_decimal(discord_user_id))
                & Key('booth_item_number').eq(booth_item_number),
        )
        items = response.get('Items', [])
        return items[0]['booth_order_number'] if items else None

    def get_booth_item_count(self, discord_user_id):
        response = self.items_table.query(
            IndexName='discord_user_id-booth_item_number-index',
            KeyConditionExpression=Key('discord_user_id').eq(_to_decimal(discord_user_id)),
            Select='COUNT',
        )
        return response.get('Count', 0)

    def _insert_discord_noti_channel(self, discord_channel_id, booth_order_number):
        try:
            self.channels_table.put_item(
                Item={
                    'booth_order_number': booth_order_number,
                    'discord_channel_id': _to_decimal(discord_channel_id),
                },
                ConditionExpression=(
                    'attribute_not_exists(booth_order_number) '
                    'AND attribute_not_exists(discord_channel_id)'
                ),
            )
            return True
        except ClientError as exc:
            if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise

    def _delete_discord_noti_channel(self, booth_order_number):
        response = self.channels_table.query(
            KeyConditionExpression=Key('booth_order_number').eq(booth_order_number)
        )
        items = response.get('Items', [])
        if not items:
            return 0
        with self.channels_table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'booth_order_number': item['booth_order_number'],
                        'discord_channel_id': item['discord_channel_id'],
                    }
                )
        return len(items)

    def _find_account_by_cookie(self, session_cookie):
        response = self.accounts_table.query(
            IndexName='session_cookie-index',
            KeyConditionExpression=Key('session_cookie').eq(session_cookie),
        )
        items = response.get('Items', [])
        if not items:
            return None
        return _to_int(items[0].get('discord_user_id'))
