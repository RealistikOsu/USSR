FROM python:3.10

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install -i https://pypi2.akatsuki.gg/cmyui/dev akatsuki-cli

COPY scripts /scripts

COPY . /srv/root
WORKDIR /srv/root

ENTRYPOINT ["/scripts/bootstrap.sh"]
