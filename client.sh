#!/bin/bash

LEADER_IP=$1
PORT=$2
CMD=$3

curl -X POST http://$LEADER_IP:$PORT/client_command \
  -H "Content-Type: application/json" \
  -d "{\"command\": \"$CMD\"}"
