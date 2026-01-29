#!/usr/bin/env bash
set -e
MEI_DIR="$HOME/dev/mei"
LOG_DIR="$MEI_DIR/logs"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
{
  echo "[$TS] MEI hourly started"
  cd "$MEI_DIR"
  MEI_MODE="hourly" /usr/bin/python3 -m core.mei_core
  echo "[$TS] MEI hourly finished"
} >> "$LOG_DIR/mei_hourly.log" 2>&1
