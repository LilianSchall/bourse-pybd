# Bourse PYBD

This project is led by @LilianSchall, @guillaumelalire and @ahmedhassayoune at
french software engineering school EPITA.

## Links
- [Archive reference](https://www.lrde.epita.fr/~ricou/pybd/projet/bourse.tgz)
- [Data to process](https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar)

## What you need to do to run the project
In a shell at the root of the repository, do the following commands:
```bash
(cd bourse/docker/analyzer && make fast);
(cd bourse/docker/dashboard && make fast);
(mkdir data && cd data && 
wget https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar &&
tar -xf boursorama.tar &&
mv boursorama.tar ..);
docker compose -f bourse/docker/docker-compose.yml up;
```
