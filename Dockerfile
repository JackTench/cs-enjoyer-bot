FROM python:3.14-slim

WORKDIR /bot

RUN pip install py-cord
# Install backport for audioop.
RUN pip install audioop-lts

COPY . /bot

CMD ["python", "main.py"]
