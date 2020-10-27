FROM python:alpine

WORKDIR /app
RUN apk add build-base git

ADD . /app
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "manage.py"]
