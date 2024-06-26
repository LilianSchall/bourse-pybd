# Bourse PYBD

This project is led by @LilianSchall, @guillaumelalire and @ahmedhassayoune at
french software engineering school EPITA.

## Links
- [Archive reference](https://www.lrde.epita.fr/~ricou/pybd/projet/bourse.tgz)
- [Data to process](https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar)

## Notes
1. The analyzer takes approximately 3 hours to fill the database.
2. For the added functionality in the dashboard, we have implemented a group of features:
   - Full screen mode for the Plotly graph
   - The ability to choose specific fixed dates for the stock graph (1D, 5D, 1M, 3M, 6M, YTD, 1Y, 5Y, ALL)
   - Percentage change of Daystocks in the table
3. The dashboard is available at the following address: [http://localhost:8050](http://localhost:8050)

## What you need to do to run the project

The following commands will setup the project and run the docker stack :
- First it will clone the boursorama tarball and decompress it into the temporary /srv/libvirt-workdir/ folder
- Then it will build the two docker images (for the analyzer and the dashboard)

The setup can be done through the following command:
```shell
    make setup
```

Afterwards, you would like to run the docker stack.
This can be done through the following command:
```shell
    make run
```

> ⚠️: Because of the infamously known bug of podman, you will probably need to run two times
the `make run` command, since the analyzer will start too soon.
This bug has been reported in one of the moodle discussion:
(https://moodle.epita.fr/mod/forum/discuss.php?d=6855#p11745)

> 🚨: In order to see some data in the dashboard, you will need to wait for the analyzer to make a first commit to the database. The first market that will be filled will be the `Amsterdam` one.

> 🚨: For better frontend compatibility please open the dashboard in chrome (or chromium if you are evaluating with the school computers).
