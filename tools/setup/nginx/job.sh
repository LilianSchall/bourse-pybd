#!/bin/sh

update_file="$VOLUME_PATH/nginx.update";


if [ -f "$update_file" ]; then
    # A new update has been pushed into the volume 
    # We need to change the default.conf file and reload nginx
    cp "$update_file" "/app/nginx.update";
    rm "$update_file";

    mv "/app/nginx.update" "/etc/nginx/conf.d/default.conf"
    nginx -s reload
fi
