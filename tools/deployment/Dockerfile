FROM alpine:3.19

WORKDIR /app

RUN apk add --update curl jq

COPY ./generate_proxy_config.sh .

ENTRYPOINT [ "/app/generate_proxy_config.sh" ]
