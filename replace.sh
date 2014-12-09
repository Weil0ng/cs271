#!/bin/bash

sed '/^IP\|^PORT\|^pid/d' ISP.py > nISP.py
sed '/^log/r replace.txt' nISP.py > ISP.py
rm nISP.py
sed '/^IP\|^PORT\|^pid/d' ModISP.py > nModISP.py
sed '/^log/r replace.txt' nModISP.py > ModISP.py
rm nModISP.py
