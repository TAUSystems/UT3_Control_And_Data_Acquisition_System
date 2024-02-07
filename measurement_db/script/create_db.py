from __future__ import annotations

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Base

def main():
    sqlalchemy_engine = get_sqlalchemy_engine()
    Base.metadata.create_all(sqlalchemy_engine)

if __name__ == "__main__":
    main()
