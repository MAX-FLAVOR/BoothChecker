FROM python:3.12-slim
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get upgrade -y
WORKDIR /root/boothchecker
COPY ./booth_discord ./
COPY ./docker/booth-discord/requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python3","__main__.py"]