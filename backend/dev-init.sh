#!/bin/bash

# Environment Variables
# /var/www/migrate-oracle-python/backend
export DPI_DEBUG_LEVEL=64
export TNS_ADMIN=/var/www/migrate-oracle-python/backend/app/keys
export LD_LIBRARY_PATH=/var/www/migrate-oracle-python/backend/oracle_home/instantclient
export PATH=/var/www/migrate-oracle-python/backend/oracle_home/instantclient:$PATH

# Start server
python3 app/server.py
