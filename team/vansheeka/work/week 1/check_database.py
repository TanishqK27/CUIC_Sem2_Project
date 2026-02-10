# Connect to Railway

from dotenv import load_.env
load_.env()  # This magically pulls the link from your .env file

# Connect to Railway
import pandas as pd
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])

# List all tables
tables_query = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
"""
tables = pd.read_sql(tables_query, engine)
print(tables)
