FROM ddp822/tango_withsdk:latest AS builder

COPY DAQClient       /app/DAQClient
COPY DeviceServer    /app/DeviceServer
COPY Firmwares       /app/Firmwares
COPY ImageProcessing /app/ImageProcessing
COPY RunControl      /app/RunControl
COPY CMakeLists.txt      /app
COPY CmakeTangoWin.cmake /app

RUN apt install -y g++ cmake ninja-build libboost-filesystem-dev libboost-serialization-dev
RUN apt install -y qt6-base-dev
RUN apt install -y qt6-3d-dev

RUN mkdir /app/build
WORKDIR /app/build
RUN cmake /app