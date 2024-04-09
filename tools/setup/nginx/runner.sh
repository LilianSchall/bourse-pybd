#!/bin/sh

run_background_job()
{
    watch -n 10 '/app/job.sh' &>/dev/null&
}

init_config_if_needed()
{
    source="/app/default.conf";
    destination="/etc/nginx/conf.d/default.conf";

    if ! [ -f "$destination" ]; then
        cp "$source" "$destination";
    fi

}

run_background_job;

exec "$@";
