FROM python:3.10-alpine

ARG DUMB_INIT='https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_x86_64'

WORKDIR /app
RUN pip install -U pip && \
    adduser -D server && \
    apk add --update curl && \
    curl -sSLo /usr/local/bin/dumb-init ${DUMB_INIT} && \
    chmod +x /usr/local/bin/dumb-init

USER server

COPY --chown=server requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=server main.py .

ENTRYPOINT [ "/usr/local/bin/dumb-init", "--" ]
CMD [ "python", "main.py" ]
