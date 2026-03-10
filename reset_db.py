from app.database import engine, Base
from app import models

def reset_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_db()
