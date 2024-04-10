FROM nginx:stable-alpine

WORKDIR /app
COPY ./nginx.conf ./default.conf
COPY ./runner.sh .
COPY ./job.sh .
COPY ./index.html /usr/share/nginx/html

EXPOSE 80

ENTRYPOINT [ "/app/runner.sh" ]

CMD ["nginx", "-g", "daemon off;"]
