#!/bin/bash

set -e

ports=( 5000 8080 8081 9001 9000 )

for p in "${ports[@]}"; do
    lsof -i :"$p" | awk 'NR!=1 {print $2}' | xargs kill -9
done

