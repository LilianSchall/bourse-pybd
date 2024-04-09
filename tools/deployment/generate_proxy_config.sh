#!/bin/sh

escape_slahes()
{
    line="$1";

    echo "$line" | sed 's/\//\\\//g';
}

insert_in_config()
{
    line="$1";
    file="$2";
    escaped_line=$(escape_slahes "$line");

    sed -i "s/^}\$/    $escaped_line\n}/" "$file";
}

branches=$(curl -s https://api.github.com/repos/LilianSchall/bourse-pybd/branches | jq -r '.[].name' | grep "^dash-")

new_config_file="./temp.conf";
loaded_config_file="$VOLUME_PATH/nginx.conf";
cp "$loaded_config_file" "$new_config_file";

for branch in $branches; do
    result=$(cat "$loaded_config_file" | grep "$branch")
    if [ -n "$result" ]; then
        continue;
    fi
    
    insert_in_config "location /$branch {" "$new_config_file";
    insert_in_config "    proxy_pass http://$branch;" "$new_config_file";
    insert_in_config "}" "$new_config_file";

    echo "Added $branch";
done

cp "$new_config_file" "$VOLUME_PATH/nginx.update";
echo "Done!";
