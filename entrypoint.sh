#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL to be ready..."
# Wait for PostgreSQL to be ready
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

echo "🗄️  Running database migrations..."

# Check if users table exists (critical table from first migration)
TABLE_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');")

ALEMBIC_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');")

if [ "$TABLE_EXISTS" = "f" ] && [ "$ALEMBIC_EXISTS" = "t" ]; then
  echo "⚠️  Tables missing but alembic_version exists - resetting migrations..."
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "DELETE FROM alembic_version;" || true
fi

# Run migrations
alembic upgrade head

echo "✅ Migrations completed!"

# Create default tenant if not exists
echo "🏢 Creating default tenant..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "INSERT INTO tenants (name, slug, is_active) VALUES ('Default Tenant', 'default', true) ON CONFLICT DO NOTHING;" > /dev/null 2>&1 || echo "Tenant already exists"
echo "✅ Default tenant ready!"

# Seed default Knowledge Base chunks
echo "📚 Seeding default KB chunks..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'
INSERT INTO kb_chunks (tenant_id, source, chunk, chunk_hash, is_current, version, created_at, updated_at)
VALUES
  -- Password Reset FAQ
  (1, 'faq.md', 'To reset your password, click "Forgot Password" on the login page and follow the instructions sent to your email.',
   md5('To reset your password, click "Forgot Password" on the login page and follow the instructions sent to your email.'),
   true, 1, NOW(), NOW()),

  -- Support Hours
  (1, 'faq.md', 'Our support team is available Monday through Friday, 9:00 AM to 6:00 PM EST. For urgent issues outside business hours, please mark your ticket as "urgent".',
   md5('Our support team is available Monday through Friday, 9:00 AM to 6:00 PM EST. For urgent issues outside business hours, please mark your ticket as "urgent".'),
   true, 1, NOW(), NOW()),

  -- Account Creation
  (1, 'getting-started.md', 'To create a new account, click the "Register" button on the login page. You will need to provide your email address and create a password (minimum 8 characters).',
   md5('To create a new account, click the "Register" button on the login page. You will need to provide your email address and create a password (minimum 8 characters).'),
   true, 1, NOW(), NOW()),

  -- Creating Tickets
  (1, 'getting-started.md', 'To create a support ticket, click the "New Ticket" button in the dashboard. Provide a clear title and description of your issue. Our AI assistant will automatically suggest solutions based on our knowledge base.',
   md5('To create a support ticket, click the "New Ticket" button in the dashboard. Provide a clear title and description of your issue. Our AI assistant will automatically suggest solutions based on our knowledge base.'),
   true, 1, NOW(), NOW()),

  -- Ticket Status
  (1, 'tickets.md', 'Ticket statuses: "open" - newly created or awaiting response, "in_progress" - being worked on by support team, "pending" - waiting for customer response, "resolved" - issue has been solved, "closed" - ticket is completed.',
   md5('Ticket statuses: "open" - newly created or awaiting response, "in_progress" - being worked on by support team, "pending" - waiting for customer response, "resolved" - issue has been solved, "closed" - ticket is completed.'),
   true, 1, NOW(), NOW()),

  -- AI Assistant
  (1, 'features.md', 'Our AI assistant automatically analyzes your support tickets and suggests relevant solutions from our knowledge base. It can provide instant responses for common questions and will escalate complex issues to human agents.',
   md5('Our AI assistant automatically analyzes your support tickets and suggests relevant solutions from our knowledge base. It can provide instant responses for common questions and will escalate complex issues to human agents.'),
   true, 1, NOW(), NOW()),

  -- Refund Policy
  (1, 'policies.md', 'Refund requests must be submitted within 30 days of purchase. Please create a support ticket with "Refund Request" in the title and include your order number and reason for the refund.',
   md5('Refund requests must be submitted within 30 days of purchase. Please create a support ticket with "Refund Request" in the title and include your order number and reason for the refund.'),
   true, 1, NOW(), NOW()),

  -- Privacy & Security
  (1, 'security.md', 'We take your privacy seriously. All data is encrypted in transit and at rest. We never share your personal information with third parties without your explicit consent. You can request data export or deletion at any time.',
   md5('We take your privacy seriously. All data is encrypted in transit and at rest. We never share your personal information with third parties without your explicit consent. You can request data export or deletion at any time.'),
   true, 1, NOW(), NOW())

ON CONFLICT (tenant_id, chunk_hash) DO NOTHING;
EOF

if [ $? -eq 0 ]; then
    echo "✅ KB chunks seeded successfully!"
else
    echo "⚠️  KB seeding failed, but continuing..."
fi

# Seed demo data if enabled
if [ "$DEMO_MODE_ENABLED" = "true" ] && [ "$DEMO_SEED_ON_STARTUP" = "true" ]; then
    echo "📦 Seeding demo data..."
    python -c "
import asyncio
from src.core.db import get_session_context
from src.core.demo_data import DemoDataSeeder

async def seed():
    async with get_session_context() as session:
        await DemoDataSeeder.seed_all(session, tenant_id=1)

asyncio.run(seed())
    " || echo "⚠️  Demo data seeding failed, but continuing..."
    echo "✅ Demo data seeded!"
fi

echo "🚀 Starting application..."
# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
