# Getting source code

GitHub: [UT3 Control and Data Acquisition](https://github.com/TAUSystems/UT3_Control_And_Data_Acquisition_System). Need Tau Systems credentials (ask Reinier) to access the source code.

```bash
git clone git@github.com:TAUSystems/UT3_Control_And_Data_Acquisition_System.git
```

For deployment where you don't need to change the code, you can use the https
```bash
git clone https://github.com/TAUSystems/UT3_Control_And_Data_Acquisition_System.git
```

# EPICS Base Installation

EPICS is designed to work on both regular PC OS and real-time OS. As, the UT3 CDAQ system relies on regular PCs, the instruction here will only address the installation process for Linux and Windows.

We provided a copy of EPICS base source in `epics/` but users can also choose to use their own installation if they have already installed `epics-base` on their system. In that case, users should modify the variables `${EPICS_BASE}` accordingly. Instructions on how to do that is in [Using existing EPICS base installation](docs/Using existing EPICS base installation.md).







