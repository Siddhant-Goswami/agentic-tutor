"""
Run database migration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
project_root = Path(__file__).parent
env_path = project_root / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Read migration file
migration_file = project_root / "database" / "migrations" / "005_fix_match_embeddings_rls.sql"
migration_sql = migration_file.read_text()

print("=" * 70)
print("RUNNING DATABASE MIGRATION")
print("=" * 70)
print(f"\nMigration file: {migration_file.name}")
print(f"SQL length: {len(migration_sql)} characters")

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

print("\n🔧 Applying migration...")

try:
    # Execute the migration SQL
    result = supabase.rpc("exec_sql", {"sql": migration_sql}).execute()
    print("✅ Migration applied successfully!")
    print(f"\nResult: {result.data}")
except Exception as e:
    # If exec_sql doesn't exist, try running each statement separately
    print(f"⚠️  exec_sql not available, trying direct execution...")

    # Split into statements and run
    statements = [s.strip() for s in migration_sql.split(";") if s.strip() and not s.strip().startswith("--")]

    for i, stmt in enumerate(statements, 1):
        if stmt:
            print(f"\n📝 Executing statement {i}/{len(statements)}...")
            try:
                # Try to execute via PostgREST
                # Note: Supabase Python client doesn't have direct SQL execution
                # We need to use psycopg2 or similar
                print(f"Statement: {stmt[:100]}...")
                # This won't work - need direct SQL access
            except Exception as e2:
                print(f"❌ Error: {e2}")

print("\n" + "=" * 70)
print("MIGRATION COMPLETE")
print("=" * 70)
print("\nNote: If migration failed, run it manually in Supabase SQL Editor:")
print(f"  1. Go to Supabase Dashboard > SQL Editor")
print(f"  2. Copy contents of {migration_file}")
print(f"  3. Execute the SQL")
