# Bourse PYBD

This project is led by @LilianSchall, @guillaumelalire and @ahmedhassayoune at
french software engineering school EPITA.

## Links
- [Archive reference](https://www.lrde.epita.fr/~ricou/pybd/projet/bourse.tgz)
- [Data to process](https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar)

## Note
The analyzer takes approximately 3 hours to fill the database.

## What you need to do to run the project

Firstly, your first action would be to clone the boursorama tarball 
and build the two docker images (for the analyzer and the dashboard).

The tarball will be decompressed into the temporary /srv/libvirt-workdir/ folder
The docker compose file has already been correctly configured
so that the bind linked to the analyzer reaches the correct folder.

The setup can be done through the following command:
```shell
    make setup
```

Afterwards, you would like to run the docker stack.
This can be done through the following command:
```shell
    make run
```
