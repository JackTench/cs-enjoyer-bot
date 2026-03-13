FROM python:3.14

WORKDIR /bot

RUN pip install py-cord
# Install backport for audioop.
RUN pip install audioop-lts

COPY . /bot

CMD ["python", "main.py"]
