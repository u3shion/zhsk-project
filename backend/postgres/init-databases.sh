#!/bin/bash

create_user_and_db() {
    local db=$1
    local user=$2
    local password=$3

    echo "Setting up user '$user'..."
    psql --username "$POSTGRES_USER" \
        -c "CREATE USER \"$user\" WITH PASSWORD '$password';" \
        2>/dev/null || echo "  User '$user' already exists, skipping."

    echo "Setting up database '$db'..."
    psql --username "$POSTGRES_USER" \
        -c "CREATE DATABASE \"$db\" OWNER \"$user\";" \
        2>/dev/null || echo "  Database '$db' already exists, skipping."

    echo "Granting schema privileges on '$db' to '$user'..."
    psql --username "$POSTGRES_USER" --dbname "$db" \
        -c "GRANT ALL ON SCHEMA public TO \"$user\";"
}

if [ -n "$USERS_DB_NAME" ] && [ -n "$USERS_DB_USER" ] && [ -n "$USERS_DB_PASSWORD" ]; then
    create_user_and_db "$USERS_DB_NAME" "$USERS_DB_USER" "$USERS_DB_PASSWORD"
fi

if [ -n "$METERS_DB_NAME" ] && [ -n "$METERS_DB_USER" ] && [ -n "$METERS_DB_PASSWORD" ]; then
    create_user_and_db "$METERS_DB_NAME" "$METERS_DB_USER" "$METERS_DB_PASSWORD"
fi

if [ -n "$ANNOUNCEMENTS_DB_NAME" ] && [ -n "$ANNOUNCEMENTS_DB_USER" ] && [ -n "$ANNOUNCEMENTS_DB_PASSWORD" ]; then
    create_user_and_db "$ANNOUNCEMENTS_DB_NAME" "$ANNOUNCEMENTS_DB_USER" "$ANNOUNCEMENTS_DB_PASSWORD"
fi
