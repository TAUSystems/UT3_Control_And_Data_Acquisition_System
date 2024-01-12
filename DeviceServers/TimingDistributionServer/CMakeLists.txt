#=============================================================================
#
# file :        CMakeLists.txt
#
# description : Solution-Level CMake
#
# project :     TimingDistributionServer
#
#=============================================================================

#
# Files for TANGOCamera TANGO class
#
set(TIMINGDISTRIBUTIONUNIT
        TimingDistributionUnit
)

set(TIMINGDISTRIBUTIONUNIT_INCLUDE
        ${TIMING_SERVER_DIR}
)

set(TIMINGDISTRIBUTIONUNIT_SRC
        ${TIMINGDISTRIBUTIONUNIT}.cpp
        ${TIMINGDISTRIBUTIONUNIT}Class.cpp
        ${TIMINGDISTRIBUTIONUNIT}StateMachine.cpp
)

#
# User additional include, link folders/libraries and source files
#
set(USER_INCL_DIR )
set(USER_LIB_DIR )
set(USER_LIBS )
set(USER_SRC_FILES )

#
# Set global info and include directories
#
set(ALL_CLASS_INCLUDE
        ${TIMINGDISTRIBUTIONUNIT_INCLUDE}
        ${USER_INCL_DIR}
)

set(SERVER_SRC
        ${TIMINGDISTRIBUTIONUNIT_SRC}
        ${USER_SRC_FILES}
        ClassFactory.cpp
        main.cpp
)

include_directories(
        ${ALL_CLASS_INCLUDE}
        ${USER_INCL_DIR}
        ${TANGO_INCLUDES}
)

#
# Device Server generation
#
set(SERVER_NAME TimingDistributionServer)
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

