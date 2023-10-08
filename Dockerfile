FROM python:3.10

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY scripts /scripts

COPY . /srv/root
WORKDIR /srv/root

ENTRYPOINT ["/scripts/bootstrap.sh"]
