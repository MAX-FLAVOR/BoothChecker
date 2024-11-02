# booth-update-checker

[![docker-build-push](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/5ignal/booth-update-checker/actions/workflows/docker-build-push.yml)

[Docker Hub](https://hub.docker.com/r/ogunarmaya/booth-update-checker)

***
### Docker-Compose
```
services:
  booth-update-checker:
    image: ogunarmaya/booth-update-checker:latest
    container_name: booth-update-checker
    volumes:
      - ./version:/root/booth-update-checker/version
      - ./archive:/root/booth-update-checker/archive
    restart: unless-stopped
```

---

### .env

```
refresh_interval = 600
discord_bot_token = "YOUR_DISCORD_BOT_TOKEN"
s3_endpoint_url = "YOUR_S3_ENDPOINT_URL"
s3_access_key_id = "YOUR_S3_ACCESS_KEY_ID"
s3_secret_access_key = "YOUR_S3_SECRET_ACCESS_KEY"
s3_bucket_name = "YOUR_S3_BUCKET_NAME"
s3_bucket_url = "YOUR_S3_BUCKET_URL"
```

---

### Font
`JetBrains Mono`

https://www.jetbrains.com/lp/mono/

`Google Noto`

https://fonts.google.com/noto
