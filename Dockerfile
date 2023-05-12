FROM python:3.10.11
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get upgrade -y
WORKDIR /root/booth-update-checker
COPY ./app.py ./
COPY ./requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python3","app.py"]