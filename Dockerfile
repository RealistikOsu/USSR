FROM python:3.10

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["/srv/root/main.py"]
