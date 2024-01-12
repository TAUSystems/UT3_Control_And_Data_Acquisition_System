#include <MariaDBController.h>
#include <boost/date_time.hpp>

MariaDBController::MariaDBController()
    : SQL_Driver(sql::mariadb::get_driver_instance()),
      DB_Connection{nullptr}, ShotData() {
}

MariaDBController::~MariaDBController() = default;

void MariaDBController::Connect() {
    sql::Properties properties({
                                       {"user", "root"},
                                       {"password", "TauSystems!2021?"}
                               });
    try {
        DB_Connection.reset(SQL_Driver->connect("jdbc:mariadb://localhost:3306/UT3Data", properties));
    } catch (sql::SQLException& e) {
        std::cerr << e.what() << std::endl;
    }
}

void MariaDBController::Disconnect() const {
    DB_Connection->close();
}

void MariaDBController::AddEntryShotRecord() const {
    try {
        auto iso_date = boost::gregorian::to_iso_extended_string(boost::gregorian::day_clock::local_day());
        auto statement = boost::format("INSERT INTO UT3Data.ShotRecord "
"(Timestamp, Date,  EnergyOnTarget, FarFieldEnergy, PulseDuration, GasJetBackPressure, GasJetPosX, GasJetPosY, GasJetPosZ, GasJetTiming, GasJetOpeningDuration, ProbeTiming, Notes,  EPointing, ESpecFront, ESpecBack) VALUES "
"(%1%,       '%2%', %3%,            %4%,            %5%,           %6%,                %7%,        %8%,        %9%,        %10%,         %11%,                  %12%,        '%13%', '%14%',    '%15%',     '%16%'   )")
                         % ShotData.timestamp                                                                            // 1
                         % iso_date                                                                                      // 2
                         % ShotData.energyOnTarget                                                                       // 3
                         % ShotData.farfieldEnergy                                                                       // 4
                         % ShotData.pulseDuration                                                                        // 5
                         % ShotData.gasjetBackpressure                                                                   // 6
                         % ShotData.gasjetX                                                                              // 7
                         % ShotData.gasjetY                                                                              // 8
                         % ShotData.gasjetZ                                                                              // 9
                         % ShotData.gasjetTiming                                                                         // 10
                         % ShotData.gasjetDuration                                                                       // 11
                         % ShotData.probeTiming                                                                          // 12
                         % ShotData.notes                                                                                // 13
                         % (boost::format{"%1%/ut3/e-diag/e-pointing/ts_%2%.tiff"}   % iso_date % ShotData.timestamp)  // 14
                         % (boost::format{"%1%/ut3/e-diag/e-spec_front/ts_%2%.tiff"} % iso_date % ShotData.timestamp)  // 15
                         % (boost::format{"%1%/ut3/e-diag/e-spec_back/ts_%2%.tiff"}  % iso_date % ShotData.timestamp); // 16
        std::unique_ptr<sql::PreparedStatement> query(DB_Connection->prepareStatement(statement.str()));
        // std::cout << statement << "\n";
        query->executeQuery();
    } catch(sql::SQLException& e){
        std::cerr << e.what() << std::endl;
    }
}
