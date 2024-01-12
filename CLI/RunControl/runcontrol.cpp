#include <runcontrol.h>
#include <ui_runcontrol.h>

RunControl::RunControl(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::RunControl)
    , DAQThread(nullptr)
    , isDAQRunning(false) {
    ui->setupUi(this);
    dataManager = new DataManager();
    dataManager->SetCallback([this](const Tango::DevULong64& timestamp) {
        EnterShotDataToDB(timestamp);
    });
    DBController = new MariaDBController();
    DBController->Connect();
}

RunControl::~RunControl() {
    if (isDAQRunning) {
        StopDAQ();
    }

    DBController->Disconnect();
    delete DAQThread;
    delete ui;
}

void RunControl::on_StartButton_clicked() {
    ReadTextFields();
    DisableUIs();
    StartDAQ();
}

void RunControl::on_StopButton_clicked() {
    StopDAQ();
    EnableUIs();
}

void RunControl::StartDAQ() {
    dataManager->ImageSourceBeginAcquisition();
    isDAQRunning = true;

    if (DAQThread != nullptr) return;

    DAQThread = new std::thread([this]() {
        while (isDAQRunning) {
            dataManager->FetchDataPackage();
        }
    });
}

void RunControl::StopDAQ() {
    isDAQRunning = false;
    if (DAQThread != nullptr) {
        if (DAQThread->joinable()) {
            DAQThread->join();
        }
    }
    dataManager->ImageSourceEndAcquisition();

    delete DAQThread;
    DAQThread = nullptr;
}

void RunControl::EnterShotDataToDB(const Tango::DevULong64& timestamp) {
    DBController->ShotData.timestamp = (long long) timestamp;
    DBController->AddEntryShotRecord();
}

void RunControl::ReadTextFields() {
    DBController->ShotData.energyOnTarget = ui->LE_EnergyOnTarget->text().toDouble();
    DBController->ShotData.farfieldEnergy = ui->LE_FarfieldEnergy->text().toDouble();
    DBController->ShotData.pulseDuration = ui->LE_PulseDuration->text().toDouble();
    DBController->ShotData.gasjetBackpressure = ui->LE_GasjetBackpressure->text().toDouble();
    DBController->ShotData.gasjetX = ui->LE_GasjetX->text().toDouble();
    DBController->ShotData.gasjetY = ui->LE_GasjetY->text().toDouble();
    DBController->ShotData.gasjetZ = ui->LE_GasjetZ->text().toDouble();
    DBController->ShotData.gasjetTiming = ui->LE_GasjetTiming->text().toDouble();
    DBController->ShotData.gasjetDuration = ui->LE_GasjetDuration->text().toDouble();
    DBController->ShotData.probeTiming = ui->LE_ProbeTiming->text().toDouble();
    DBController->ShotData.notes = ui->LE_Notes->toPlainText().toStdString();
}

void RunControl::DisableUIs() {
    ui->LE_EnergyOnTarget->setEnabled(false);
    ui->LE_FarfieldEnergy->setEnabled(false);
    ui->LE_PulseDuration->setEnabled(false);
    ui->LE_GasjetBackpressure->setEnabled(false);
    ui->LE_GasjetX->setEnabled(false);
    ui->LE_GasjetY->setEnabled(false);
    ui->LE_GasjetZ->setEnabled(false);
    ui->LE_GasjetTiming->setEnabled(false);
    ui->LE_GasjetDuration->setEnabled(false);
    ui->LE_ProbeTiming->setEnabled(false);
    ui->LE_Notes->setEnabled(false);
}

void RunControl::EnableUIs() {
    ui->LE_EnergyOnTarget->setEnabled(true);
    ui->LE_FarfieldEnergy->setEnabled(true);
    ui->LE_PulseDuration->setEnabled(true);
    ui->LE_GasjetBackpressure->setEnabled(true);
    ui->LE_GasjetX->setEnabled(true);
    ui->LE_GasjetY->setEnabled(true);
    ui->LE_GasjetZ->setEnabled(true);
    ui->LE_GasjetTiming->setEnabled(true);
    ui->LE_GasjetDuration->setEnabled(true);
    ui->LE_ProbeTiming->setEnabled(true);
    ui->LE_Notes->setEnabled(true);
}

