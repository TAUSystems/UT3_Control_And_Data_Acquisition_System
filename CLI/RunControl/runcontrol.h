#pragma once

#include <QMainWindow>
#include <DataManager.h>
#include <MariaDBController.h>

QT_BEGIN_NAMESPACE
namespace Ui { class RunControl; }
QT_END_NAMESPACE

class RunControl : public QMainWindow {
    Q_OBJECT

public:
    explicit RunControl(QWidget *parent = nullptr);
    ~RunControl() override;

private slots:

    void on_StartButton_clicked();
    void on_StopButton_clicked();
    void StartDAQ();
    void StopDAQ();
    void EnterShotDataToDB(const Tango::DevULong64 &);
    void ReadTextFields();

    void DisableUIs();
    void EnableUIs();

private:
    Ui::RunControl *ui;
    DataManager* dataManager;
    bool isDAQRunning;
    std::thread* DAQThread;
    MariaDBController* DBController;
};
