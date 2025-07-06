#!/bin/bash

#  Get the absolute path of the current script
LOCAL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Environment Variables
# /home/luis122448/Desktop/repository-tsi/py-migrate-oracle/py-etl-oracle
export DPI_DEBUG_LEVEL=64
export TNS_ADMIN=/home/luis122448/Desktop/repository-tsi/migrate-oracle-python/backend/app/wallet
export LD_LIBRARY_PATH=/home/luis122448/Desktop/repository-tsi/migrate-oracle-python/backend/oracle_home/instantclient

# Exporting environment variables
source ~/.bashrc

# Restar Virtual Environment
deactivate
source .venv/bin/activate

# Start server
python app/server.py
