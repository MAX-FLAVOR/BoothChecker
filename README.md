# BoothChecker

[![latest](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/latest-build.yml/badge.svg)](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/latest-build.yml)
[![dev](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/dev-build.yml/badge.svg)](https://github.com/MAX-FLAVOR/BoothChecker/actions/workflows/dev-build.yml)

***
### Docker-Compose
```
services:
  booth-checker:
    image: ogunarmaya/booth-checker:latest
    volumes:
      - ./version:/root/boothchecker/version
      - ./archive:/root/boothchecker/archive
      - ./config.json:/root/boothchecker/config.json
    depends_on:
      - booth-discord
    environment:
      - OPENAI_API_KEY="YOUR_OPENAI_API_KEY" #Optional
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
      
  booth-discord:
    image: ogunarmaya/booth-discord:latest
    volumes:
      - ./version:/root/boothchecker/version
      - ./config.json:/root/boothchecker/config.json
    depends_on:
      - chrome
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  chrome:
    image: selenium/standalone-chrome:latest
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### config.json

```
{
    "refresh_interval": 600,
    "discord_api_url": "http://booth-discord:5000",
    "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN",
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

---

### Font
`JetBrains Mono`

https://www.jetbrains.com/lp/mono/

`Google Noto`

https://fonts.google.com/noto
