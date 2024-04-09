FROM nginx:stable-alpine

WORKDIR /app
COPY ./nginx.conf ./default.conf
COPY ./runner.sh .
COPY ./index.html /usr/share/nginx/html

EXPOSE 80

CMD [ "/app/runner.sh" ]

