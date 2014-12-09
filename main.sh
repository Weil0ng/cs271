#!/bin/bash

echo "1 for ISPaxos, 2 for MSPaxos"

read -e c

if [ "$c" == '1' ] 
then
  echo "Launching ISP client"
  ./ISP.py
else
  echo "Launching ModISP client"
  ./ModISP.py
fi
