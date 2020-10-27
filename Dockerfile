FROM python:alpine

WORKDIR /app
ADD . /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "manage.py"]