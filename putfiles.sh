#!/bin/bash
cd Client
for f in `ls *.py`;
   do sudo ampy --port /dev/ttyUSB0 put $f 
   echo "Done putting: $f";
done;
