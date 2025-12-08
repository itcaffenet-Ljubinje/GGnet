#!/bin/bash
set -e

echo "🚀 Starting GGnet Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import asyncio
from sqlalchemy import text
from app.core.database import get_async_engine

async def wait_for_db():
    engine = get_async_engine()
    max_retries = 30
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text('SELECT 1'))
            print('✓ Database is ready!')
            return
        except Exception as e:
            if i < max_retries - 1:
                print(f'⏳ Database not ready, retrying in {retry_delay}s... ({i+1}/{max_retries})')
                time.sleep(retry_delay)
            else:
                print(f'✗ Database connection failed after {max_retries} attempts')
                raise

asyncio.run(wait_for_db())
"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Initialize admin user (optional - can be done manually)
# Note: Admin user should be created using: python scripts/create_admin.py
# This is skipped in Docker to allow manual admin setup
echo "ℹ️  Admin user initialization skipped in Docker. Use 'python scripts/create_admin.py' to create admin user."

# Start the application
echo "✓ Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

