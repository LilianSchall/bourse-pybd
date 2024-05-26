# Bourse PYBD

This project is led by @LilianSchall, @guillaumelalire and @ahmedhassayoune at
french software engineering school EPITA.

## Links
- [Archive reference](https://www.lrde.epita.fr/~ricou/pybd/projet/bourse.tgz)
- [Data to process](https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar)

## Note
1. The analyzer takes approximately 3 hours to fill the database.
2. For the added functionality in the dashboard, we have implemented a group of features:
   - Full screen mode for the Plotly graph
   - The ability to choose specific fixed dates for the stock graph (1D, 5D, 1M, 3M, 6M, YTD, 1Y, 5Y, ALL)
   - Percentage change of Daystocks in the table

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

Because of the infamously known bug of podman, you will need to run two times
this command, since the analyzer will start too soon.
This bug has been reported in one of the moodle discussion:
(https://moodle.epita.fr/mod/forum/discuss.php?d=6855#p11745)
