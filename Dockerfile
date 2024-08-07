FROM python:3.9

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Requirements
COPY ./requirements/main.txt /app/requirements.txt
RUN python3.9 -m pip install -r /app/requirements.txt

# Scripts
COPY ./scripts /app/scripts

# Application.
COPY ./ussr /app/ussr

RUN chmod +x -R /app/scripts
ENTRYPOINT [ "/app/scripts/bootstrap.sh" ]
