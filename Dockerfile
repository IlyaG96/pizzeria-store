FROM python:3.9.10-alpine

WORKDIR /usr/src/pizzeria-bot
COPY requirements.txt /usr/src/pizzeria-bot/

RUN pip install --no-cache-dir -r requirements.txt
COPY . .


ENTRYPOINT ["python"]
CMD ["request_to_devman.py"]