FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

RUN touch logfile.txt

ENV HOST=${RM_HOST} \
    PORT=${RM_PORT} \
    USER=${RM_USER} \
    PASSWORD=${RM_PASSWORD} \
    TOKEN=${TOKEN} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_HOST=${DB_HOST} \
    DB_PORT=${DB_PORT} \
    DB_DATABASE=${DB_DATABASE}

CMD ["python", "./bot.py"]
