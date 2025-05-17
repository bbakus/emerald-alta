from sqlalchemy import create_engine, inspect
from app.models import Base, NPC
import os

# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'emerald_altar.db')
engine_url = f'sqlite:///{db_path}'

engine = create_engine(engine_url)
inspector = inspect(engine)

# Create only the NPC table if it doesn't exist
print("Creating NPC table if it doesn't exist...")
if 'npcs' not in inspector.get_table_names():
    NPC.__table__.create(engine)
    print("NPC table created successfully!")
else:
    print("NPC table already exists.")

print("Database update complete!") 