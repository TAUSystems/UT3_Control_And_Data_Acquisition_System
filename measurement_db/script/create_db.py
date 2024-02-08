from __future__ import annotations

from argparse import ArgumentParser

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Base

def main(drop=False):
    sqlalchemy_engine = get_sqlalchemy_engine()
    if drop:
        Base.metadata.drop_all(sqlalchemy_engine)
    Base.metadata.create_all(sqlalchemy_engine)

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument('--drop', action='store_true', 
                    help="Drop all tables before create. Otherwise create_db.py "
                    "only creates the tables not yet present in the database."
                   )
    args = ap.parse_args()
    main(drop=args.drop)
