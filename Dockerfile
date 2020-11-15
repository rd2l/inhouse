FROM python:3.8

WORKDIR /app
RUN apk add build-base git libffi-dev

ADD . /app
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

ENTRYPOINT ["python", "manage.py"]
