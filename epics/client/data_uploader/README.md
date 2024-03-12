# Data uploader client
Monitors image and scalar EPICS process variables and upload them to the image
backend and measurement database respectively.

## Install & Usage
The most straightforward way to install this project is with Poetry, which is 
described below, but a few alternatives will be given as well. 

In all cases, the prerequisites are: 
* *MariaDB Connector/C*.  Follow instructions to [configure the MariaDB repository](https://mariadb.com/docs/server/connect/programming-languages/c/install/#CS_Package_Repository) and [install the MariaDB Connector/C](https://mariadb.com/docs/server/connect/programming-languages/c/install/#Install_on_Debian,_Ubuntu)
  

### Virtual environment with Poetry
First install [Poetry](https://python-poetry.org/docs/1.7/#installing-with-the-official-installer). 
Then, from a terminal window inside this `epics/client/data_uploader` directory, 
run 
```bash
poetry install
```

This will create a virtual environment and install the project and necessary 
dependencies into it, including the `measurement_db` project. 

You can now start the client by running
```bash
poetry run python run.py
```

### Globally with Poetry
As one alternative, the project can be installed without the use of a virtual 
environment. This makes sense when installing into a container that will only 
contain this client (although this will run just as well in a virtual environment 
in a container)

As above, install [Poetry](https://python-poetry.org/docs/1.7/#installing-with-the-official-installer). 
Then, from this directory in a terminal, configure poetry not to use a virtual 
environment, and then install the project.
```bash
poetry config virtualenvs.create false
poetry install
```

Then you can start the client by running
```bash
python3 run.py
```

If during the install you get an error saying 
`Invalid version '1.1build1' on package distro-info`, 
this appears to be because the `distro-info` package, installed by Ubuntu, does
not have a version number format that is supported by Python. I solved the issue 
by uninstalling the `apt` package `python3-distro-info`. This is probably OK 
because in this scenario of a global install, we aren't planning to install anything
else after this.

### Globally or virtual environment with pip
If you cannot use Poetry, or if you want to install globally but the previous 
didn't work, you can install the project with `pip`, but be warned that you will 
likely get different versions of packages than what this project has been tested 
with! 

If creating a virtual environment, run 
```bash
virtualenv venv   # or virtualenv /path/to/where/you/want/venv
source venv/bin/activate   # or on Windows: venv\Scripts\activate
```

Then, from this directory, run 
```bash
pip install .
``` 

## Building the Docker image
First, because this project depends on a project elsewhere in this repository, and 
files can't be copied from parents of the current directory, the `docker build` 
command needs to be run from the root of this repository. 

Second, the image backend endpoint needs to be sent to the `docker build` command 
as a build argument. 

Altogether: 
```bash
docker build \
  -f epics/client/data_uploader/Dockerfile \
  -t data-uploader \
  --build-arg IMAGE_BACKEND_ENDPOINT_URL=http://12.34.56.78:1234/daq-image \
  .
```

Since EPICS isn't installed outright in this container, the CA library can't 
spawn its own `caRepeater` process, so it's important (I think?) that `caRepeater` is running 
elsewhere if the host runs multiple clients. See 
[CA Repeater in EPICS Channel Access reference manual](https://epics.anl.gov/base/R3-15/5-docs/CAref.html#Repeater). 
