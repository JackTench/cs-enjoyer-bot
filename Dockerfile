FROM python:3.14

WORKDIR /bot

RUN pip install py-cord

COPY . /bot

CMD ["python", "main.py"]
