import logging
import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


logger = logging.getLogger('BoothChecker')


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_int(value):
    if isinstance(value, Decimal):
        return int(value)
    return value


class BoothDynamoDB:
    def __init__(self, config, retries=5, delay=2):
        self.config = config
        self.dynamodb = self._connect_with_retry(config, retries, delay)
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
                    logger.error("DynamoDB 연결에 실패했습니다. 설정을 확인해주세요.")
                    raise
                logger.warning(
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

    def get_booth_items(self):
        items = []
        scan_kwargs = {}
        while True:
            response = self.items_table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
            scan_kwargs['ExclusiveStartKey'] = last_key

        joined_rows = []
        for item in items:
            discord_user_id = _to_int(item.get('discord_user_id'))
            account = self.accounts_table.get_item(
                Key={'discord_user_id': _to_decimal(discord_user_id)}
            ).get('Item')
            if not account:
                continue

            channels = self.channels_table.query(
                KeyConditionExpression=Key('booth_order_number').eq(item['booth_order_number'])
            ).get('Items', [])
            for channel in channels:
                joined_rows.append(
                    (
                        item.get('booth_order_number'),
                        item.get('booth_item_number'),
                        item.get('item_name'),
                        item.get('intent_encoding'),
                        item.get('download_number_show', True),
                        item.get('changelog_show', True),
                        item.get('archive_this', False),
                        item.get('gift_item', False),
                        item.get('summary_this', False),
                        item.get('fbx_only', False),
                        account.get('session_cookie'),
                        discord_user_id,
                        _to_int(channel.get('discord_channel_id')),
                    )
                )

        return joined_rows
