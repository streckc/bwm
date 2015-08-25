#!/bin/bash

MINUTES=5
INTERFACE="eth1"

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ROOT_PATH=$(cd $SCRIPT_PATH/.. && pwd)
CAP_PATH="$ROOT_PATH/process"
LCK_FILE="$CAP_PATH/cap.lck"


mkdir -p "$CAP_PATH"

sudo tcpdump -n -w "$CAP_PATH/cap_%Y%m%d%H%M%S.pcap" -G $(($MINUTES*60)) -i $INTERFACE -s 128 -z "$ROOT_PATH/bin/move_to_process.bash"

