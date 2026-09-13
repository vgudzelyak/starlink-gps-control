#!/bin/bash

process=$(ps aux | grep '[s]tarlink-gps-control/main.py')
logfile="$(pwd)/starlink-gps-control.log"
main="$(pwd)/main.py"

if [[ -z $process ]]; then
        echo -e "\n$(date +"%Y-%m-%d %T.%N") Process not found. Starting..." >> $logfile
        python3 $main &
fi