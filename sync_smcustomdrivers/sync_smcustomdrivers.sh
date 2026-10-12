#!/bin/bash

# Source DB
SRC_DB="$HOME/.var/app/org.kde.kstars/data/kstars/userdb.sqlite"

# Destination DB
DST_DB="$HOME/.indi/profiles.db"

# Clear destination table
sqlite3 "$DST_DB" <<EOF
DELETE FROM custom;
EOF

# Migrate data from source to destination (excluding id and manufacturer)
sqlite3 "$DST_DB" <<EOF
ATTACH DATABASE 'file:$SRC_DB?mode=ro' AS src;

INSERT INTO custom (label, name, family, exec, version)
SELECT
    Label,
    Name,
    Family,
    Exec,
    Version
FROM src.customdrivers;

DETACH DATABASE src;
EOF

echo "Data migration completed."
