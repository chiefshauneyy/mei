#!/usr/bin/env bash
set -e

MEI_DIR="$HOME/dev/mei"
LOG_DIR="$MEI_DIR/logs"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo "[$TS] MEI run started"
  cd "$MEI_DIR"
  /usr/bin/python3 -m core.mei_core
  echo "[$TS] MEI run finished"
} >> "$LOG_DIR/mei.log" 2>&1
