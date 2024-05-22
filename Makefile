all: setup run

setup:
	(cd bourse/docker/analyzer && make fast);
	(cd bourse/docker/dashboard && make fast);
	(mkdir -p /srv/libvirt-workdir/bourse/data &&\
	 cd /srv/libvirt-workdir/bourse/data &&\
	 wget https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar &&\
	 tar -xf boursorama.tar &&\
	 rm -rf boursorama.tar);

run:
	(cd bourse/docker && docker compose up);


