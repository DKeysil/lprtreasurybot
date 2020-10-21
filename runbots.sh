#!/bin/bash
list_bots=$(ls bots/)
base_dir=$(pwd)"/bots"
echo $list_bots
for bot_dir in $list_bots
do
cd $base_dir"/"$bot_dir
pwd
git pull
docker-compose -f docker-compose.yml -f docker-compose.creds.yml up -d --build
done
cd ../..
