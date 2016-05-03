#!/bin/bash

# Use > 1 to consume two arguments per pass in the loop (e.g. each
# argument has a corresponding value to go with it).
# Use > 0 to consume one or more arguments per pass in the loop (e.g.
# some arguments don't have a corresponding value to go with it such
# as in the --default example).
# note: if this is set to > 0 the /etc/hosts part is not recognized ( may be a bug )

usage() {
cat << EOF

This script must be run with super-user privileges.

The script executing the following tasks:
- Change hostname
- Execute pre-install script.
- Execute post-install script.

Usage:$(basename $0) [arguments]
	-v --verbose:	Display more information to the output.
	-o --original:	Original hostname
	-n --new:	New hostname
EOF
}

#VERBOSE=false

while [[ $# > 1 ]]
do
key="$1"


case $key in
    -h|--help)
    usage
    exit 0
    ;;
    -v|--verbose)
    VERBOSE=true
    #shift # past argument
    ;;
    -o|--original)
    ORIGINAL_HOST="$2"
    shift # past argument
    ;;
    -n|--new)
    NEW_HOST="$2"
    shift # past argument
    ;;
    -b|--before)
    PRE_INSTALL_SCRIPT="$2"
    shift # past argument
    ;;
    -a|--after)
    POST_INSTALL_SCRIPT="$2"
    ;;
    *)
    exit 0
            # unknown option
    ;;
esac
shift # past argument or value
done

if [ -z "$VERBOSE" ]; then
    echo 'Create temporary directory.'
fi


mkdir -p tmp
cd tmp
cp /etc/hostname ./hostname.bak
cp /etc/hosts ./hosts.bak
chown `whoami`:`whoami` ./*.bak

echo "Change hostname from ${ORIGINAL_HOST} to ${NEW_HOST}"
sed 's/'"${ORIGINAL_HOST}"'/'"${NEW_HOST}"'/g' hostname.bak > hostname
sed 's/'"${ORIGINAL_HOST}"'/'"${NEW_HOST}"'/g' hosts.bak > hosts

cp ./hostname /etc/hostname
cp ./hosts /etc/hosts

cd ..
echo "Execute pre-install script: ${PRE_INSTALL_SCRIPT}"
sudo -u `whoami` sh ${PRE_INSTALL_SCRIPT} > ./tmp/${PRE_INSTALL_SCRIPT}.log
echo "Execute post-install script: ${POST_INSTALL_SCRIPT}"
sudo -u `whoami` sh ${POST_INSTALL_SCRIPT} > ./tmp/${POST_INSTALL_SCRIPT}.log

echo "Cleanup temporary files."
rm -r ./tmp
