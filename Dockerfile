FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

COPY ./ /ai-bot
WORKDIR /ai-bot

RUN pip3 install -r requirements.txt

CMD ["python3", "aibot.py"]