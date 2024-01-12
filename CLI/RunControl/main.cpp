#include "runcontrol.h"

#include <QApplication>

int main(int argc, char *argv[]) {
    QApplication a(argc, argv);
    RunControl w;
    w.show();
    return a.exec();
}
