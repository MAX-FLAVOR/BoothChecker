FROM python:3.11.4-slim
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get upgrade -y
WORKDIR /root/booth-update-checker
COPY ./booth_checker ./
COPY ./fonts ./fonts
COPY ./requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python3","__main__.py"]