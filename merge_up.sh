#!/bin/bash
git remote add upstream https://github.com/OpenDroneMap/WebODM.git
git fetch upstream
git checkout upstream #master
git merge upstream/master
git push

git checkout master
git merge upstream

#Resolve any conflicts
#git push
