# BoothChecker

[![latest](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/latest-build.yml/badge.svg)](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/latest-build.yml)
[![develop](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/develop-build.yml/badge.svg)](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/develop-build.yml)

BOOTH.pm의 아이템 업데이트를 주기적으로 확인하고 업데이트 감지 시 Discord Bot으로 메세지를 전송합니다.

---

### config.json

```
{
    "refresh_interval": 600,
    "selenium_url": "http://chrome:4444/wd/hub",
    "dynamodb": {
        "region": "ap-northeast-2",
        "endpoint_url": "https://dynamodb.ap-northeast-2.amazonaws.com",
        "tables": {
            "accounts": "booth_accounts",
            "items": "booth_items",
            "channels": "discord_noti_channels"
        }
    },
    "discord_api_url": "http://booth-discord:5000",
    "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN",
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "s3":
        {
            "endpoint_url": "YOUR_S3_ENDPOINT_URL",
            "bucket_name": "YOUR_S3_BUCKET_NAME",
            "bucket_access_url": "YOUR_S3_BUCKET_ACCESS_URL",
            "access_key_id": "YOUR_S3_ACCESS_KEY_ID",
            "secret_access_key": "YOUR_S3_SECRET_ACCESS_KEY"
        }
}
```

#### `s3` (선택사항)

changelog.html을 S3에 업로드하고, Discord Embed에서 마스킹된 링크로 제공합니다.

`s3`를 사용하지 않을 경우, `s3` 부분을 제거하면 됩니다. 이 경우 changelog.html은 Discord에 직접 업로드됩니다.

#### 'gemini_api_key' (선택사항)

변경점을 Google Gemini를 통해 요약합니다.

---

### Font
`JetBrains Mono`

https://www.jetbrains.com/lp/mono/

`Google Noto`

https://fonts.google.com/noto
