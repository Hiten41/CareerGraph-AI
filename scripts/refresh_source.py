import argparse
from pathlib import Path
from app.db.session import Session
from app.ingestion.sources import JsonSnapshot, refresh

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Import an authorized local source. Only pass --expire-missing for a complete snapshot."
    )
    p.add_argument("source")
    p.add_argument("file", type=Path)
    p.add_argument("--expire-missing", action="store_true")
    args = p.parse_args()
    with Session.begin() as db:
        print(refresh(db, args.source, JsonSnapshot(args.file), args.expire_missing))
