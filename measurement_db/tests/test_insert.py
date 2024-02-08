import unittest
from datetime import datetime

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Burst, Shot, Measurement

from sqlalchemy import Insert, Delete, Table
from sqlalchemy.orm import declarative_base

class TestInsert(unittest.TestCase):
    def setUp(self) -> None:
        self.sqlalchemy_engine = get_sqlalchemy_engine()
        self.burst_datetime = datetime.now()
        self.shot_datetime = datetime.now()

        with self.sqlalchemy_engine.begin() as conn:
            conn.execute( Insert(Burst).values({'timestamp': self.burst_datetime, 'scan': None, 'seq': 0}) )
            conn.execute( Insert(Shot).values({'timestamp': self.shot_datetime, 'burst': self.burst_datetime, 'seq': 0}) )

        return super().setUp()

    def test_insert(self):
        """ Copied from image-processing-backend/applications/rq_worker/result_handlers/db.py
        """
        measurement_table_insert = Table("measurement", declarative_base().metadata, autoload_with=self.sqlalchemy_engine).insert()
        device_name = 'test'
        scalars = {'key1': 1.23,
                   'key2': float('nan'),
                  }

        with self.sqlalchemy_engine.begin() as conn:
            conn.execute(measurement_table_insert.values(shot=self.shot_datetime),
                         [{'measurement_name': f"{device_name}:{measurement_name}",
                           'value': float(measurement_value),
                          } for measurement_name, measurement_value in scalars.items()
                         ]
                        )

    def tearDown(self) -> None:
        with self.sqlalchemy_engine.begin() as conn:
            conn.execute( Delete(Measurement).where(Measurement.shot == self.shot_datetime) )
            conn.execute( Delete(Shot).where(Shot.timestamp == self.shot_datetime) )
            conn.execute( Delete(Burst).where(Burst.timestamp == self.burst_datetime) )

        return super().tearDown()

if __name__ == "__main__":
    unittest.main()
