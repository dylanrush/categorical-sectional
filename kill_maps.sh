#!/bin/bash
#
# Kills any StratuxHud processes hanging arround.
# Useful for making sure the REST ports are clear
# and nothing is left over.
sudo kill -9 $(sudo ps -ef | grep -i "controller.py" | grep -v "grep" |  awk '{print $2}' | tac)
