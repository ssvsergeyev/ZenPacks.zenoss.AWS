#!/bin/bash

POLL_TIME=10

while true
do
    zenmodeler run -d EC2Manager 
    sleep $POLL_TIME
done

# while true
# do
#     zenec2modeler.py -f -t
#     if [ $? -eq 10 ]; then
#         zenmodeler run -d EC2Manager 
#     fi
#     sleep $POLL_TIME
# done