#!/bin/bash

NAME="<service_name>"                     # Name of the service, will be used in another vars
WORK_DIR="/opt/${NAME}"               # Working directory where the service will be started, defaults to /var/lib/${NAME}
USER=<service_owner>                                # User that will spawn the process, defaults to the service name
GROUP=<space_owner>                               # Group that will spawn the process, defaults to the service name
LOG_PATH=${WORK_DIR}/log                   # Standard output and Standard error will be outputted here

DAEMON="/usr/bin/<service_daemon>"      # Path to the service executable, e.g. /usr/bin/java
DAEMON_ARGS="<service_daemon_args>"  # Arguments passed to the service startup

PIDFILE=${WORK_DIR}/${NAME}.pid              # Pid file location, defaults to /var/run/${NAME}.pid
SCRIPTNAME=/etc/init.d/$NAME              # Location of this init script

adduser ${USER}
adduser ${USER} ${GROUP}
ln -s /home/${USER} ${WORK_DIR}
su -u ${USER} mkdir ${LOG_PATH}
echo "Output ..." > ${LOG_PATH}/${NAME}.out
echo "Error ..." > ${LOG_PATH}/${NAME}.err
cp /home/${USER}/${NAME} /etc/init.d
chmod a+x /etc/init.d/${NAME}
update-rc.d ${NAME} defaults
service ${NAME} start
