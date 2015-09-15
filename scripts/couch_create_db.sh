#!/bin/bash

# soledad-server will call this script with
#   "sudo -u soledad-admin /usr/local/bin/couch_create_db.sh <DBNAME>"

# path to netrc file with admin credetials
NETRC='/etc/couchdb/couchdb-admin.netrc'
URL='http://127.0.0.1:5984'
SUDO='sudo -u soledad-admin'

db_unsanitized="$1"

# sanitize input to prevent command injection
# i.e. an attacker should not cause harm calling
# this from soledad-server using an input of i.e.
# "; rm -rf /"
# A bit of bashucation:
# bash itself does a good job by default,
# a good overview can be found at
# http://stackoverflow.com/a/4273137
# however, restricting to alphanumeric chars here
# is always a good idea
db="${db_unsanitized//[^a-zA-Z0-9]/}"

if [ -z "${db}" ]
then
  echo "Please specify a database name to create !"
  exit 1
fi

cmd="/usr/bin/curl -s --netrc-file ${NETRC} -X PUT ${URL}/${db}"


result=$(${cmd})

if [ "$result" != '{"ok":true}' ]
then
  echo "Error - \"${cmd}\" did not succeed, this was the return code:"
  echo "${result}"
  exit 1
fi

