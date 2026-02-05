"""
Database Explorer Script
========================
Run this in Google Colab to dump all database schema and statistics.
The output will be saved to 'db_exploration.json' which gets downloaded automatically.

Usage in Colab:
1. Open a new Colab notebook or use an existing one
2. Copy-paste this entire script into a cell
3. Run the cell
4. A JSON file will be downloaded automatically
"""

# Install dependencies (only needed in Colab)
import subprocess
import sys
try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "psycopg2-binary"])
    import psycopg2

import json
from datetime import datetime, date
from decimal import Decimal

# Database connection
DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def json_serializer(obj):
    """Handle non-serializable types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def run_query(query):
    """Run a SQL query and return results as list of dicts."""
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    cur = conn.cursor()
    cur.execute(query)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

def run_scalar(query):
    """Run a query and return single value."""
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()[0]
    conn.close()
    return result

print("=" * 60)
print("DATABASE EXPLORATION")
print("=" * 60)

exploration = {
    "generated_at": datetime.now().isoformat(),
    "database_url": "Railway PostgreSQL (IP restricted)",
    "tables": {},
    "summary": {}
}

# Get all tables
print("\n1. Discovering tables...")
tables = run_query("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
table_names = [t['table_name'] for t in tables]
print(f"   Found {len(table_names)} tables: {', '.join(table_names)}")

# Get detailed info for each table
print("\n2. Analyzing each table...")
for table_name in table_names:
    print(f"\n   [{table_name}]")

    table_info = {
        "columns": [],
        "row_count": 0,
        "sample_data": [],
        "statistics": {}
    }

    # Get columns
    columns = run_query(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    table_info["columns"] = columns
    print(f"      Columns: {len(columns)}")

    # Get row count
    try:
        count = run_scalar(f"SELECT COUNT(*) FROM {table_name}")
        table_info["row_count"] = count
        print(f"      Rows: {count:,}")
    except Exception as e:
        table_info["row_count"] = f"Error: {e}"
        print(f"      Rows: Error - {e}")

    # Get sample data (first 5 rows)
    try:
        sample = run_query(f"SELECT * FROM {table_name} LIMIT 5")
        table_info["sample_data"] = sample
        print(f"      Sample: {len(sample)} rows")
    except Exception as e:
        table_info["sample_data"] = []
        print(f"      Sample: Error - {e}")

    # Get basic statistics for numeric/timestamp columns
    stats = {}
    for col in columns:
        col_name = col['column_name']
        col_type = col['data_type']

        try:
            if col_type in ['integer', 'bigint', 'numeric', 'real', 'double precision']:
                stat = run_query(f"""
                    SELECT
                        MIN({col_name}) as min_val,
                        MAX({col_name}) as max_val,
                        AVG({col_name}::numeric) as avg_val
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                """)
                if stat:
                    stats[col_name] = stat[0]
            elif 'timestamp' in col_type or col_type == 'date':
                stat = run_query(f"""
                    SELECT
                        MIN({col_name}) as min_val,
                        MAX({col_name}) as max_val
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                """)
                if stat:
                    stats[col_name] = stat[0]
        except:
            pass

    table_info["statistics"] = stats
    exploration["tables"][table_name] = table_info

# Summary statistics
print("\n3. Generating summary...")
exploration["summary"] = {
    "total_tables": len(table_names),
    "table_row_counts": {name: exploration["tables"][name]["row_count"] for name in table_names}
}

# Save to file
output_file = "db_exploration.json"
with open(output_file, 'w') as f:
    json.dump(exploration, f, indent=2, default=json_serializer)

print(f"\n{'=' * 60}")
print(f"COMPLETE! Saved to {output_file}")
print(f"{'=' * 60}")

# Auto-download in Colab
try:
    from google.colab import files
    files.download(output_file)
    print("\nFile download started!")
except ImportError:
    print(f"\nNot running in Colab. File saved to: {output_file}")

# Also print a summary
print("\n" + "=" * 60)
print("QUICK SUMMARY")
print("=" * 60)
for name, info in exploration["tables"].items():
    cols = ", ".join([c["column_name"] for c in info["columns"][:5]])
    if len(info["columns"]) > 5:
        cols += f" ... (+{len(info['columns'])-5} more)"
    print(f"\n{name} ({info['row_count']:,} rows)")
    print(f"  Columns: {cols}")
