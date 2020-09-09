#!/bin/bash
#
# Nemesis - Powerful  Telegram group managment bot
# Copyright (C) 2017 - 2019 Paul Larsen
# Copyright (C) 2019 - 2020 KaratekHD
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

if [ "$EUID" -ne 0 ]
  then echo "ERROR: Please run as root"
  # exit
fi
echo "WARNING: THIS SCRIPT WILL CREATE A CONFIG FILE AND INSTALL ALL REQUIREMENTS; YOU STILL HAVE TO SETUP A DATABASE!"
# shellcheck disable=SC1068
BOOL=true
while $BOOL; do
  read -p "QUESTION: Do you wish to install this program? [y/n] " yn
    case $yn in
        [Yy]* ) BOOL=false; break;;
        [Nn]* ) exit;;
        * ) echo "ERROR: Please answer yes or no.";;
    esac
done
if [ -f /etc/os-release ]
then
  if grep -q openSUSE "/etc/os-release"; then
    echo "INFO: Running on openSUSE. Great!"
  else
    echo "ERROR: This script only supports openSUSE. Exiting."
    exit
  fi
else
  echo "ERROR: /etc/os-release doesn't exist. Aborting."
  exit
fi
RPM=$(rpm -q python38-base)
if echo "$RPM" | grep -q "not installed"; then
  echo "INFO: Python is not installed on your system. Installing...";
  zypper install --recommends --no-confirm python38-base
else
  echo "INFO: Python 3 is installed on your system. Great!";
fi
RPM=$(rpm -q python3-pip)
if echo "$RPM" | grep -q "not installed"; then
  echo "INFO: PIP3 is not installed on your system. Installing...";
  zypper install --recommends --no-confirm python3-pip
else
  echo "INFO: PIP3 is installed on your system. Great!";
fi
RPM=$(rpm -q gcc)
if echo "$RPM" | grep -q "not installed"; then
  echo "INFO: GCC is not installed on your system. Installing...";
  zypper install --recommends --no-confirm gcc
else
  echo "INFO: GCC is installed on your system. Great!";
fi
echo "Installing requirements...."
pip3 install -r requirements.txt
