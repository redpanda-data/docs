#!/bin/bash

echo "Please enter the name of the first branch:"
read branch1
echo "Please enter the name of the second branch:"
read branch2

git fetch
git diff --summary $branch1..$branch2 -- ./modules/
