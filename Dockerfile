FROM python:3.11

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/osuAkatsuki/akatsuki-cli

COPY scripts /scripts

COPY . /srv/root
WORKDIR /srv/root

ENTRYPOINT ["/scripts/bootstrap.sh"]
