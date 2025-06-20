FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install supervisor gunicorn
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["supervisord", "-c", "supervisord.conf"]
