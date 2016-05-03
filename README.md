# loki-machine

## 3rd party components of the development chain

### Virtualenv

A Virtual Environment is a tool to keep the dependencies required by different projects in separate places, by creating virtual Python environments for them. It solves the “Project X depends on version 1.x but, Project Y needs 4.x” dilemma, and keeps your global site-packages directory clean and manageable.

To use virtualenv follow [this guide](http://docs.python-guide.org/en/latest/dev/virtualenvs/)

### [Fabric](http://www.fabfile.org/)

Fabric is a Python library and command-line tool for streamlining the use of SSH for application deployment or systems administration tasks.

The project build tasks uses Fabric macke changes on your linux based workstations.

## Usage

### Install environment & create space on the endpoints (initial install)
```bash
fab -u pi -p raspberry -H 10.114.62.242,10.114.62.243,10.114.62.244 clean_install
```

### Deploy our source code to the endpoints (development, continously)
```bash
fab -u pi -p raspberry -H 10.114.62.242,10.114.62.243,10.114.62.244 deploy_scripts
```

### Setup & start the system (post-install tasks)
```bash
fab -u pi -p raspberry -H 10.114.62.242,10.114.62.243,10.114.62.244 init_system
```
