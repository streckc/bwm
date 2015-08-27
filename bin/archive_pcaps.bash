#!/bin/bash

FILES_TO_PROCESS=1

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ROOT_PATH=$(cd $SCRIPT_PATH/.. && pwd)
COMPLETE_PATH="$ROOT_PATH/done"
PROCESS_PATH="$ROOT_PATH/process"
TMP_FILE="$PROCESS_PATH/arch_cap.$$"
LCK_FILE="$PROCESS_PATH/arch_cap.lck"

log_msg() { echo $(date +"%Y/%m/%d %H:%M:%S")": $1"; }

mkdir -p "$COMPLETE_PATH"

if [ -f "${LCK_FILE}" ]; then
	log_msg "Lock file exists. Exiting. ($LCK_FILE)"
	exit
fi
touch "${LCK_FILE}"

cd "${COMPLETE_PATH}"
DATE=$(date +"%Y%m%d")
ls *.pcap 2>/dev/null | egrep -v "^cap_${DATE}" | awk -v fileprefix="$TMP_FILE" '
{
	tfn=$0
	gsub(/^cap_/, "", tfn)
	fn=fileprefix".lst."substr(tfn, 0, 9)
	print $0 > fn
}
'
for LIST_FILE in $(ls $TMP_FILE.lst.* 2>/dev/null); do
	TAR_FILE=$(basename $LIST_FILE | sed -e 's/^.*.lst./archive_/' -e 's/$/.tar.gz/')
	echo $LIST_FILE $TAR_FILE
	if [ -f "$TAR_FILE" ]; then
		echo "need to append/replace"
	else
		log_msg "Archiving old pcaps to ${TAR_FILE}."
		tar --create --file "${TAR_FILE}" --gzip --files-from "${LIST_FILE}" --remove-files
	fi
done
rm -f ${TMP_FILE}*
rm -f ${LCK_FILE}*
log_msg "Done."
