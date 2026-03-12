FROM python:3.14

WORKDIR /bot

RUN pip install py-cord

COPY *.py ./

CMD ["python", "main.py"]
