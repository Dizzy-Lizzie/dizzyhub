#!/bin/bash

### Run the container locally for testing purposes
docker build -t dzpg .

docker run --rm --name dzpg  \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_USER='lizzie' \
    -e POSTGRES_DB='lizzie' \
    postgres;