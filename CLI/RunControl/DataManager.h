#pragma once

#include <string>
#include <functional>
#include <memory>
#include <mutex>
#include <vector>
#include <future>
#include <iterator>
#include <thread>
#include <tango.h>
#include <conncpp.hpp>
#include <boost/format.hpp>

class DataSource : public Tango::CallBack {
public:
    Tango::DeviceProxy* TANGODevice;
    std::function<void(const std::string&)> callback;
    std::string AttributeName;
    Tango::DevULong64 Timestamp;

    DataSource(const std::string& deviceName, const std::string& attributeName);
    DataSource(const DataSource& other);
    DataSource(DataSource&& other) noexcept ;
    DataSource& operator=(const DataSource& other);
    DataSource& operator=(DataSource&& other) noexcept ;

    void SetCallback(const std::function<void(const std::string&)>& cb);
    void push_event(Tango::DataReadyEventData*) override;
};

class DataManager {
private:
    std::mutex mutex;
    std::vector<DataSource*> sources;
    Tango::DevULong64 Timestamp;
    std::function<void(const Tango::DevULong64&)> callback;

public:
    DataManager();
    void SetCallback(const std::function<void(const Tango::DevULong64&)>& cb);
    void FetchDataPackage();
    void ImageSourceBeginAcquisition();
    void ImageSourceEndAcquisition();
};



