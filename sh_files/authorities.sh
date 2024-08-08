#!/bin/bash

run_commands() {
    local authority=$1
    gnome-terminal -- bash -c "\
        docker exec -it martsia_ethereum_container bash -c ' \
            sleep 0.3 && \
            cd MARTSIA-demo/sh_files && \
            sleep 0.3 && \
            sh old/authority.sh --authority $authority; \
	    sleep 10 && \
            sh old/server_authority.sh --authority $authority; \
            bash' \
        "
}
filename="../src/.env"
count=$(grep -c '^[^#]*''NAME="AUTH' "$filename")
for ((i=1; i<=$count; i++)); do
    run_commands $i
done

