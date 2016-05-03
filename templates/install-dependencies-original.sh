#!/bin/bash

SUPERUSER=lordoftheflies
DEPLOYMENTS_DIR=/home/lordoftheflies/Documents/bme/project-laboratory
DRUID_VERSION=0.8.3
ZOOKEEPER_VERSION=3.4.6
INSTALL_DIR=${DEPLOYMENTS_DIR}

# Download & configure ZooKeeper
echo "Install Zookeeper ${ZOOKEEPER_VERSION} ..."
cd ${INSTALL_DIR}
curl http://www.gtlib.gatech.edu/pub/apache/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/zookeeper-${ZOOKEEPER_VERSION}.tar.gz -o zookeeper-${ZOOKEEPER_VERSION}.tar.gz
tar xzf zookeeper-${ZOOKEEPER_VERSION}.tar.gz
cd zookeeper-${ZOOKEEPER_VERSION}
cp conf/zoo_sample.cfg conf/zoo.cfg
echo "Zookeeper installed successfully to ${INSTALL_DIR}/zookeeper-${ZOOKEEPER_VERSION}."

# Download & configure Druid
echo "Install Druid ${DRUID_VERSION} ..."
cd ${INSTALL_DIR}
curl http://static.druid.io/artifacts/releases/druid-${DRUID_VERSION}-bin.tar.gz -o druid-${DRUID_VERSION}.tar.gz
tar xzf druid-${DRUID_VERSION}.tar.gz
cd druid-${DRUID_VERSION}
mkdir ./log
echo "Druid installed successfully to ${INSTALL_DIR}/druid-${DRUID_VERSION}."
cp ${DEPLOYMENTS_DIR}/common.runtime.properties ${INSTALL_DIR}/druid-${DRUID_VERSION}/config/_common/

# Download & configure Pivot UI
cd ${INSTALL_DIR}
echo "Install Pivot ..."
sudo npm i -g imply-pivot
echo "Pivot installed successfully."

# Setup deployments
sudo ln -s ${DEPLOYMENTS_DIR}/zookeeper-${ZOOKEEPER_VERSION} /opt/zookeeper
sudo ln -s ${DEPLOYMENTS_DIR}/druid-${DRUID_VERSION} /opt/druid

# Setup LSB services
sudo cp ${DEPLOYMENTS_DIR}/scripts/lsb-services/loki_* /etc/init.d
sudo chmod u+x /etc/init.d/loki_*
cd ${INSTALL_DIR}/druid-${DRUID_VERSION}
echo "Druid coordinator-node output ..." > loki_coordinator.out
echo "Druid coordinator-node error ..." > loki_coordinator.err
echo "Druid broker-node output ..." > loki_broker.out
echo "Druid broker-node error ..." > loki_broker.err
echo "Druid historical-node output ..." > loki_historical.out
echo "Druid historical-node error ..." > loki_historical.err
echo "Druid realtime-node output ..." > loki_realtime.out
echo "Druid realtime-node error ..." > loki_realtime.err

sudo update-rc.d loki_* defaults

# Setup metadata storage
sudo -u postgres createuser druid -P
sudo -u postgres createdb druid -O druid
