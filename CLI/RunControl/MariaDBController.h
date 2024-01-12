#pragma once

#include <conncpp.hpp>
#include <boost/format.hpp>

struct ShotData_t {
    long long timestamp;
    double energyOnTarget;
    double farfieldEnergy;
    double pulseDuration;
    double gasjetBackpressure;
    double gasjetX;
    double gasjetY;
    double gasjetZ;
    double gasjetTiming;
    double gasjetDuration;
    double probeTiming;
    std::string notes;
};

class MariaDBController {
public:
    MariaDBController();
    ~MariaDBController();

    void Connect();
    void Disconnect() const;
    void AddEntryShotRecord() const;

    std::unique_ptr<sql::Driver> SQL_Driver;
    std::unique_ptr<sql::Connection> DB_Connection;
    ShotData_t ShotData;
};
