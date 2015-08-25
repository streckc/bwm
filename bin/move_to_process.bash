#!/bin/bash

FILE=$1
USER="streckc"

SCRIPT_PATH=$(dirname $BASH_SOURCE)
ROOT_PATH=$(cd $SCRIPT_PATH/.. && pwd)
PROC_PATH="$ROOT_PATH/to_process"

mkdir -p "$PROC_PATH"

mv "$FILE" "$PROC_PATH"
chown "$USER" "$PROC_PATH/$(basename $FILE)"

