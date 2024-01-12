use UT3Data;

create table ShotRecord
(
    ShotID                int unsigned auto_increment comment 'Unique shot ID'
        primary key,
    Timestamp             bigint unsigned not null comment 'Linux timestamp of event',
    Date                  date            null comment 'Date of shot',
    EnergyOnTarget        float           null comment 'Laser pulse energy on target in Joules',
    FarFieldEnergy        float           null comment 'Farfield energy in mJ',
    PulseDuration         float           null comment 'Pulse duration in femtoseconds',
    GasJetBackPressure    float           null comment 'Gas jet back pressure in Bars',
    GasJetPosX            float           null comment 'Gas jet relative position (x) in microns',
    GasJetPosY            float           null comment 'Gas jet relative position (y) in microns',
    GasJetPosZ            float           null comment 'Gas jet relative position (z) in microns',
    GasJetTiming          float           null comment 'Gas jet opening to main pulse in milliseconds',
    GasJetOpeningDuration float           null comment 'Gas jet opening duration in milliseconds',
    ProbeTiming           float           null comment 'Probe to main pulse in picoseconds',
    Notes                 varchar(400)    null comment 'Notes on shot',
    EPointing             varchar(200)    null comment 'Relative path to pointing screen images',
    ESpecFront            varchar(200)    null comment 'Relative path to electron spectrometer front screen',
    ESpecBack             varchar(200)    null comment 'Relative path to electron spectrometer back screen'
)
    comment 'Shot record';

