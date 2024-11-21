FROM python:3.9

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get clean

WORKDIR /app

RUN mkdir src
RUN mkdir drive

WORKDIR /app/src

COPY src/requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip/*

COPY src/ .

RUN chmod +x app.py && chmod +x wsgi.py  && chmod +x start_api.sh

ENTRYPOINT [ "./start_api.sh"]