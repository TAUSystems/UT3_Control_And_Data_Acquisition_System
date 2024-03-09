from __future__ import annotations

from argparse import ArgumentParser

from measurement_db.utils import get_sqlalchemy_engine
from measurement_db.orm.tables import Base
from measurement_db.orm.tables import Variable, ImageDevice
from measurement_db.orm.tables import VariableSource, EPICSAccessProtocol
from sqlalchemy.orm import Session as SQLAlchemySession

def create_tables(drop=False):
    sqlalchemy_engine = get_sqlalchemy_engine()
    if drop:
        Base.metadata.drop_all(sqlalchemy_engine)
    Base.metadata.create_all(sqlalchemy_engine)

def insert_data():
   
    # ## define variables and image devices
    variables = []
    image_devices = []

    # gasjet position
    variables.extend([
        Variable(name=f"Plasma:Position:{axis}:{metric}", 
                 source=VariableSource.fetch, 
                 epics_access_protocol=EPICSAccessProtocol.channel_access
                )
        for metric in ['Status_GET', 'Absolute_GET', 'Absolute_RBV', 'Offset', 'Inverted', 
                    'Relative_GET', 'Relative_RBV',
                    'Acceleration_GET', 'MaxVelocity_GET', 'MinVelocity_GET',
                    ]
        for axis in ['HorizontalX', 'VerticalY', 'LongitudinalZ']
    ])

    # pressure control
    variables.extend([
        Variable(name=f"Plasma:PressureControl:{metric}", 
                 source=VariableSource.fetch, 
                 epics_access_protocol=EPICSAccessProtocol.channel_access
                )
        for metric in ['Mode_GET', 'Channel_GET', 'Pressure_SET', 'Pressure_RBV', 
                       'Rate_GET', 'Rate_RBV', 'Is_Channel_Stable', 'Is_Rate_Stable'
                      ]
    ])

    # electron spectrometer
    image_devices.extend([
        ImageDevice(name=f"E:Spectrometer:{screen}", image_pv_name=f"E:Pva:Spectrometer:{screen}:Image")
        for screen in ['Pointing', 'LowEnergy', 'HighEnergy']
    ])


    # insert them
    with SQLAlchemySession(get_sqlalchemy_engine()) as sa_session:
        for variable in variables:
            sa_session.add(variable)
        for image_device in image_devices:
            sa_session.add(image_device)
        
        sa_session.commit()


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument('--drop', action='store_true', 
                    help="Drop all tables before create. Otherwise create_db.py "
                    "only creates the tables not yet present in the database."
                   )
    args = ap.parse_args()
    create_tables(drop=args.drop)
    insert_data()
