#=============================================================================
#
# file :        CMakeLists.txt
#
# description : Solution-Level CMake
#
# project :     FLIRCamera
#
#=============================================================================

#
# Files for FLIRCamera TANGO class
#
set(FLIRCAMERA
        FLIRCamera
)
set(FLIRCAMERA_INCLUDE
        ${FLIR_SERVER_DIR}
)
set(FLIRCAMERA_SRC
        ${FLIR_SERVER_DIR}/${FLIRCAMERA}.cpp
        ${FLIR_SERVER_DIR}/${FLIRCAMERA}.h
        ${FLIR_SERVER_DIR}/${FLIRCAMERA}Class.cpp
        ${FLIR_SERVER_DIR}/${FLIRCAMERA}Class.h
        ${FLIR_SERVER_DIR}/${FLIRCAMERA}StateMachine.cpp
)

#
# User additional include, link folders/libraries and source files
#
set(SPINNAKER_DIR
        /opt/spinnaker
)

set(USER_INCL_DIR
        ${SPINNAKER_DIR}/include
        ${Boost_INCLUDE_DIRS}
)

set(USER_LIB_DIR
        ${SPINNAKER_DIR}/lib
        ${Boost_LIBRARY_DIRS}
)

set(USER_LIBS
        Spinnaker
        ${Boost_LIBRARIES}
)

set(USER_SRC_FILES
)

#
# Set global info and include directories
#
set(ALL_CLASS_INCLUDE
        ${FLIRCAMERA_INCLUDE}
        ${USER_INCL_DIR}
)
set(SERVER_SRC
        ${FLIRCAMERA_SRC}
        ${USER_SRC_FILES}
        ClassFactory.cpp
        main.cpp)

include_directories(
        ${ALL_CLASS_INCLUDE}
        ${USER_INCL_DIR}
        ${TANGO_INCLUDES}
)

#
# Device Server generation
#
set(SERVER_NAME FLIRServer)
#
#	Set library directories
#
link_directories(${USER_LIB_DIR} ${TANGO_LIB_HOME})

#
#	Compile and link
#
message("SERVER_NAME=${SERVER_NAME}")
message("SERVER_SRC=${SERVER_SRC}")
add_executable(${SERVER_NAME} ${SERVER_SRC})
if(ENABLE_DEBUG_FEATURES)
    target_compile_definitions(${SERVER_NAME} PRIVATE ENABLE_DEBUG_FEATURES)
endif()
target_link_libraries(${SERVER_NAME} ${USER_LIBS} ${TANGO_LIBS})

