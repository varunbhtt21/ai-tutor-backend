#!/bin/bash

# Migration management script for AI Tutor Backend

source .venv/bin/activate

case "$1" in
    "create")
        if [ -z "$2" ]; then
            echo "Usage: ./migrations.sh create 'migration_message'"
            exit 1
        fi
        echo "Creating migration: $2"
        alembic revision --autogenerate -m "$2"
        ;;
    "upgrade")
        echo "Running database migrations..."
        alembic upgrade head
        ;;
    "downgrade")
        if [ -z "$2" ]; then
            echo "Downgrading to previous migration..."
            alembic downgrade -1
        else
            echo "Downgrading to: $2"
            alembic downgrade "$2"
        fi
        ;;
    "history")
        echo "Migration history..."
        alembic history
        ;;
    "current")
        echo "Current migration version..."
        alembic current
        ;;
    "init")
        echo "Creating initial migration..."
        alembic revision --autogenerate -m "Initial migration"
        ;;
    *)
        echo "Usage: ./migrations.sh {create|upgrade|downgrade|history|current|init}"
        echo ""
        echo "Commands:"
        echo "  create 'message'  - Create new migration"
        echo "  upgrade          - Apply all pending migrations"
        echo "  downgrade [rev]  - Rollback migrations"
        echo "  history          - Show migration history"
        echo "  current          - Show current migration"
        echo "  init             - Create initial migration"
        exit 1
        ;;
esac 