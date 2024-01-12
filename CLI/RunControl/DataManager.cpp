#include <DataManager.h>

#include <utility>

DataSource::DataSource(const std::string& deviceName, const std::string& attributeName) :
callback(nullptr),
AttributeName(attributeName),
Timestamp(0) {
    try {
        TANGODevice = new Tango::DeviceProxy(deviceName.c_str());
        TANGODevice->subscribe_event(AttributeName, Tango::DATA_READY_EVENT, this);
        std::cout << "GUI client connected to " << TANGODevice->dev_name() << "\n";
    } catch(Tango::DevFailed &e){
        Tango::Except::print_exception(e);
        throw;
    }
}

void DataSource::SetCallback(const std::function<void(const std::string&)>& cb) {
    this->callback = cb;
}

void DataSource::push_event(Tango::DataReadyEventData*) {
    try {
        if (AttributeName == "Timestamp") {
            Tango::DevVarULong64Array* attr_val;
            TANGODevice->read_attribute(AttributeName) >> attr_val;
            Timestamp = (*attr_val)[0];
            delete attr_val;
        }
        callback(TANGODevice->name());
    } catch(Tango::DevFailed &e){
        Tango::Except::print_exception(e);
        throw;
    }
}

DataSource::DataSource(const DataSource &other) {
    TANGODevice = other.TANGODevice;
    callback = other.callback;
    AttributeName = other.AttributeName;
    Timestamp = other.Timestamp;
}

DataSource::DataSource(DataSource &&other) noexcept {
    TANGODevice = other.TANGODevice;
    callback = std::move(other.callback);
    AttributeName = std::move(other.AttributeName);
    Timestamp = other.Timestamp;
}

DataSource &DataSource::operator=(const DataSource &other) {
    TANGODevice = other.TANGODevice;
    callback = other.callback;
    AttributeName = other.AttributeName;
    Timestamp = other.Timestamp;
    return *this;
}

DataSource &DataSource::operator=(DataSource &&other) noexcept {
    TANGODevice = other.TANGODevice;
    callback = std::move(other.callback);
    AttributeName = std::move(other.AttributeName);
    Timestamp = other.Timestamp;
    return *this;
}

DataManager::DataManager() : Timestamp(0), callback(nullptr) {
    sources.clear();
    // TODO: Add all data sources here
    sources.push_back(new DataSource("ut3/timing/tdu", "Timestamp"));
    sources.push_back(new DataSource("ut3/e-diag/e-pointing", "image"));
    sources.push_back(new DataSource("ut3/e-diag/e-spec_front", "image"));
    sources.push_back(new DataSource("ut3/e-diag/e-spec_back", "image"));
}

void DataManager::FetchDataPackage() {
    int dataReceivedCount = 0;

    auto Callback = [&](const std::string& deviceName) {
        std::lock_guard<std::mutex> lock(mutex);
        dataReceivedCount++;
        if (deviceName == "ut3/timing/tdu") Timestamp = sources.at(0)->Timestamp;
        if (dataReceivedCount == sources.size()) callback(Timestamp);
    };

    for (auto& aSource : sources) {
        if (!aSource->callback) aSource->SetCallback(Callback);
    }

    unsigned int sleep_cycle = 0;
    while (dataReceivedCount < sources.size() && sleep_cycle < 10) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        sleep_cycle++;
    }
}

void DataManager::SetCallback(const function<void(const Tango::DevULong64 &)> &cb) {
    this->callback = cb;
}

void DataManager::ImageSourceBeginAcquisition() {
    for (unsigned int i = 1; i < sources.size(); i++) {
        try {
            // auto state = sources.at(i)->TANGODevice->command_inout("State");
            sources.at(i)->TANGODevice->command_inout_asynch("BeginAcquisition");
        } catch(Tango::DevFailed &e){
            Tango::Except::print_exception(e);
            throw;
        }
    }
}

void DataManager::ImageSourceEndAcquisition() {
    for (unsigned int i = 1; i < sources.size(); i++) {
            try {
                // auto state = sources.at(i)->TANGODevice->command_inout("State");
                sources.at(i)->TANGODevice->command_inout_asynch("EndAcquisition");
            } catch(Tango::DevFailed &e){
                Tango::Except::print_exception(e);
                throw;
            }
    }
}


