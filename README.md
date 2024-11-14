# booth-update-checker

[![docker-build-push](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml)

[Docker Hub](https://hub.docker.com/r/ogunarmaya/booth-update-checker)

***
### Docker-Compose
```
services:
  booth-checker:
    image: ogunarmaya/booth-checker:latest
    volumes:
      - ./version:/root/booth-update-checker/version
      - ./archive:/root/booth-update-checker/archive
      - ./config.json:/root/booth-update-checker/config.json
    networks:
      - booth-network
    depends_on:
      - booth-discord
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
      
  booth-discord:
    image: ogunarmaya/booth-discord:latest
    volumes:
      - ./version:/root/booth-update-checker/version
      - ./config.json:/root/booth-update-checker/config.json
    networks:
      - booth-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  booth-network:
    driver: bridge
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
