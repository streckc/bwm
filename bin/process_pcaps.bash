#!/bin/bash

FILES_TO_PROCESS=1

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ROOT_PATH=$(cd $SCRIPT_PATH/.. && pwd)
CAP_PATH="$ROOT_PATH/to_process"
PROCESS_PATH="$ROOT_PATH/process"
COMPLETE_PATH="$ROOT_PATH/done"
DB_PATH="$SCRIPT_PATH"
LCK_FILE="$PROCESS_PATH/proc_cap.lck"

log_msg() { echo $(date +"%Y/%m/%d %H:%M:%S")": $1"; }

mkdir -p "$CAP_PATH"
mkdir -p "$PROCESS_PATH"
mkdir -p "$COMPLETE_PATH"

if [ -f "${LCK_FILE}" ]; then
	log_msg "Lock file exists. Exiting. ($LCK_FILE)"
	exit
fi
touch "${LCK_FILE}"

while true; do
	$SCRIPT_PATH/load_pcap.py -d "$DB_PATH/net_mon.db" "${CAP_PATH}"
	sleep 60
done

rm -f ${LCK_FILE}*
log_msg "Done."
