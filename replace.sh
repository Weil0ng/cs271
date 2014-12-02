#!/bin/bash

sed '/^IP\|^PORT/d' CmdInterpreter.py > nCmdInterpreter.py
sed '/log/r replace.txt' nCmdInterpreter.py > CmdInterpreter.py
rm nCmdInterpreter.py
