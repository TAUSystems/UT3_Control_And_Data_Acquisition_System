#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <math.h>

#include <epicsTypes.h>
#include <epicsTime.h>
#include <epicsThread.h>
#include <epicsString.h>
#include <epicsTimer.h>
#include <epicsMutex.h>
#include <epicsEvent.h>
#include <iocsh.h>

#include "PS3000A.h"
#include <epicsExport.h>

#define PS3000A_FREQUENCY 1000000000

#define MAX_ENUM_STRING_SIZE 20

static const char *driverName="PS3000A";
void RunTask(void *drvPvt);

static const uint16_t input_ranges[] = {
	10,
	20,
	50,
	100,
	200,
	500,
	1000,
	2000,
	5000,
	10000,
	20000,
	50000
};

static const char *ps3000a_strings[] = {
	"OK",
	"Max units opened",
	"Memory fail",
	"Not found",
	"Firmware fail",
	"Open operation in progress",
	"Operation failed",
	"Not responding",
	"Config fail",
	"Kernel driver too old",
	"EEPROM corrupt",
	"OS not supported",
	"Invalid handle",
	"Invalid parameter",
	"Invalid timebase",
	"Invalid voltage range",
	"Invalid channel",
	"Invalid trigger channel",
	"Invalid condition channel",
	"No signal generator",
	"Streaming failed",
	"Block mode failed",
	"NULL parameter",
	"ETS mode set",
	"Data not available",
	"String buffer too small",
	"ETS not supported",
	"Auto trigger time too short",
	"Buffer stall",
	"Too many samples",
	"Too many segments",
	"Pulse width qualifier",
	"Delay",
	"Source details",
	"Conditions",
	"User callback",
	"Device sampling",
	"No samples available",
	"Segment out of range",
	"Busy",
	"Start index invalid",
	"Invalid info",
	"Info unavailable",
	"Invalid sample interval",
	"Trigger error",
	"Memory",
	"Signal generator parameter",
	"Shot sweeps warning",
	"Signal generator trigger source",
	"Aux output conflict",
	"Aux output ets conflict",
	"Warning ext threshold conflict",
	"Warning aux output conflict",
	"Signal generator over voltage",
	"Delay null",
	"Invalid buffer",
	"Signal generator offset voltage",
	"Signal generator peak to peak",
	"Cancelled",
	"Segment not used",
	"Invalid call",
	"Get values interrupted",
	"Not used",
	"Invalid sample ratio",
	"Invalid state",
	"Not enough segments",
	"Driver function",
	"Reserved",
	"Invalid coupling",
	"Buffers not set",
	"Ratio mode not supported",
	"Rapid not supported in aggregation",
	"Invalid trigger property",
	"Interface not connected",
	"Resistance and probe not allowed",
	"Power failed",
	"Signal generator waveform setup failed",
	"FPGA fail",
	"Power manager",
	"Invalid analog offset",
	"PLL lock failed",
	"Analog board",
	"Config fail AWG",
	"Initialise FPGA",
	"External frequency invalid",
	"Clock change error",
	"Trigger and external clock clash",
	"PWQ and external clock clash",
	"Unable to open scaling file",
	"Memory clock frequency",
	"I2C not responding",
	"No captures available",
	"Too many trigger channels in use",
	"Invalid trigger direction",
	"Invalid trigger states",
	"Not used in this capture mode",
	"Get data active",
	"IP networked",
	"Invalid IP address",
	"Ipsocket failed",
	"Ipsocket timeout",
	"Settings failed",
	"Network failed",
	NULL
};


/** Constructor for the PS3000A class.
  * Calls constructor for the asynPortDriver base class.
  * \param[in] portName The name of the asyn port driver to be created.
  * \param[in] maxPoints The maximum  number of points in the volt and time arrays */
PS3000A::PS3000A(const char *portName, int maxPoints) : 
asynPortDriver(portName,
1, /* maxAddr */
asynInt32Mask | asynFloat64Mask | asynFloat64ArrayMask | asynEnumMask | asynDrvUserMask, /* Interface mask */
asynInt32Mask | asynFloat64Mask | asynFloat64ArrayMask | asynEnumMask,  /* Interrupt mask */
0,
1, /* Autoconnect */
0, /* Default priority */
0) /* Default stack size*/ {
    asynStatus status;
    const char *functionName = "PS3000A";

    /* Make sure maxPoints is positive */
    if (maxPoints < 1) maxPoints = 1000;

    /* Allocate the output waveform array */
    pData_[0] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));
    pData_[1] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));

    /* Allocate the waveform array (pico scope delivers int16_t array */
    data_buffer[0] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */
    data_buffer[1] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */

    /* Allocate the time base array */
    pTimeBase_ = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));
    eventId_ = epicsEventCreate(epicsEventEmpty);

	createParam(P_RunString             , asynParamInt32       , &P_Run             ); // 1
	createParam(P_MaxPointsString       , asynParamInt32       , &P_MaxPoints       ); // 2  
	createParam(P_PicoConnectString     , asynParamInt32       , &P_PicoConnect     ); // 3
	createParam(P_PicoConnectedString   , asynParamInt32       , &P_PicoConnected   ); // 4
	createParam(P_SampleLengthString    , asynParamInt32       , &P_SampleLength    ); // 5
	createParam(P_SampleFrequencyString , asynParamInt32       , &P_SampleFrequency ); // 6
	createParam(P_TriggerSourceString   , asynParamInt32       , &P_TriggerSource   ); // 7
	createParam(P_ChannelRangeStringA   , asynParamInt32       , &P_ChannelRangeA   ); // 8
	createParam(P_ChannelRangeStringB   , asynParamInt32       , &P_ChannelRangeB   ); // 9
	createParam(P_TimeBaseString        , asynParamFloat64Array, &P_TimeBase        ); // 10
	createParam(P_SamplingIntervalString, asynParamFloat64     , &P_SamplingInterval); // 11
	createParam(P_WaveformStringA       , asynParamFloat64Array, &P_WaveformA       ); // 12
	createParam(P_WaveformStringB       , asynParamFloat64Array, &P_WaveformB       ); // 13

    /* Set the initial values of some parameters */
	setIntegerParam(P_Run,               0);
	setIntegerParam(P_MaxPoints,         maxPoints);
	setIntegerParam(P_PicoConnect,       0);
    setIntegerParam(P_PicoConnected,     0);
	setIntegerParam(P_SampleLength,      maxPoints);
	setIntegerParam(P_SampleFrequency,   PS3000A_FREQUENCY);
	setIntegerParam(P_TriggerSource,     2);

	ps.max_points = maxPoints;
    ps.max_value = 32512;

	setIntegerParam(P_ChannelRangeA, (int) PS3000A_1V);
	setIntegerParam(P_ChannelRangeB, (int) PS3000A_50MV);
	ps.config.ch[0].range = PS3000A_1V;
	ps.config.ch[0].range_v = input_ranges[ps.config.ch[0].range];
	ps.config.ch[1].range = PS3000A_100MV;
	ps.config.ch[1].range_v = input_ranges[ps.config.ch[1].range];

	printf("Starting Init\n");

	// Do this once at initialization
	SetTimeBase();
    SetTimeBaseArray();

    /* Create the thread that runs the waveforms acq in the background */
    status = (asynStatus)(epicsThreadCreate("PS3000ATask", epicsThreadPriorityMedium, epicsThreadGetStackSize(epicsThreadStackMedium), (EPICSTHREADFUNC)::RunTask, this) == NULL);
    if (status) {
        printf("%s:%s: epicsThreadCreate failure\n", driverName, functionName);
        return;
    }
}

void PS3000A::SetTimeBaseArray() {
	int i;
	epicsInt32 max_points = 0;
	getIntegerParam(P_MaxPoints, &max_points);
	printf("SetTimeBaseArray()\n");
	printf("Time interval = %fns\n", ps.time_interval_ns);
	printf("Max points = %d\n", max_points);
	for (i = 0; i < max_points; ++i) pTimeBase_[i] = (double)i * (double) ps.time_interval_ns;
	doCallbacksFloat64Array(pTimeBase_, max_points,	P_TimeBase, 0);
}

void RunTask(void *drvPvt) {
    PS3000A *pPvt = (PS3000A *)drvPvt;
    pPvt->RunTask();
}

void pico_block_ready(int16_t handle, PICO_STATUS ok, void *p_parameter) {
	struct BlockInfo *info = (struct BlockInfo *)p_parameter;
	if (ok != PICO_CANCELLED) info->ready = 1;
}

void PS3000A::RunTask() {
	epicsInt32 run;

	lock();

	while(1) {
		getIntegerParam(P_Run, &run);
		unlock();
		lock();
		getIntegerParam(P_Run, &run);
		if (!run) continue;
		PicoRunBlock();
	}
}

int PS3000A::PicoRunBlock() {

	//FIXME: need to take care of this function
	PICO_STATUS ok;

	epicsInt32 max_points;
	getIntegerParam(P_MaxPoints, &max_points);

	/* Trigger time is at 40 % of the screen */
	float trigger_fraction = 0.4;
	int32_t pre_trigger = max_points * (1. - trigger_fraction);
	int32_t post_trigger = max_points - pre_trigger;
	/* time_indisposed_ms: on exit, the time, in milliseconds, that the scope will spend collecting samples. 
	This does not include any auto trigger timeout. If this pointer is null, nothing will be written here. */
	int32_t time_indisposed_ms = 0; 
	/* callback_block_ready: a pointer to the ps3000aBlockReady callback function that the driver will call when
	the data has been collected. To use the ps3000aIsReady polling method instead of a callback
	function, set this pointer to NULL. */
	ps3000aBlockReady callback_block_ready = pico_block_ready;
	/* p_parameter: a void pointer that is passed to the ps3000aBlockReady callback function.
	The callback can use this pointer to return arbitrary data to the application */
	struct BlockInfo block_info;
	block_info.ready = 0;
	void *p_parameter = (void *)&block_info;
	int cnt = 0;
	const int trigger_timeout = 60000; /* ms (set to 1 min just in case the IOC waits for trigger indefinitely) */
	PS3000A_RATIO_MODE down_sample_ratio_mode = PS3000A_RATIO_MODE_NONE;
	uint32_t n_samples = max_points;
	uint32_t start_index = 0;
	uint32_t segment_index = 0;
	ok = ps3000aRunBlock(ps.handle, pre_trigger, post_trigger, ps.time_base, 0, &time_indisposed_ms, segment_index, callback_block_ready, p_parameter);
	CHKOK("RunBlock");

	/* Waiting for trigger... */

	/* If no trigger within timeout period */
	cnt = 0;
	while (block_info.ready == 0) {
		epicsThreadSleep(1e-3);
		cnt++;
		if (cnt == trigger_timeout) {
			printf("No trigger in %d ms\n", trigger_timeout);
			return 44;
		}
	}

	/* If triggered */
	if (block_info.ready == 1) {
		int i;
		uint32_t ch;
		double val;
		int64_t time;
		PS3000A_TIME_UNITS time_units;
		int16_t overflow = 0;

		/* Get the data */
		ok = ps3000aGetValues(ps.handle, start_index, &n_samples, 1, down_sample_ratio_mode, segment_index, &overflow);
		CHKOK("GetValues");

		ok = ps3000aGetTriggerTimeOffset64(ps.handle, &time, &time_units, segment_index);
		CHKOK("GetTriggerTimeOffset");

		for (ch = 0; ch < 2; ++ch) {
			for (i = start_index; i < max_points; ++i) {
				val = adc_to_uv(data_buffer[ch][i], ch) / 1e6;
				pData_[ch][i] = val;
			}
			if (ch == 0) {
        		doCallbacksFloat64Array(pData_[ch], max_points, P_WaveformA, 0);
			} else {
				doCallbacksFloat64Array(pData_[ch], max_points, P_WaveformB, 0);
			}
		}
        callParamCallbacks();
	} else {}

	
	return 0;
}

int PS3000A::OpenPS3000A() {
	PICO_STATUS ok;
	int8_t *serial = 0;

	ps.config.ch[0].coupling = PS3000A_DC;

	ok = ps3000aOpenUnit(&ps.handle, serial);
	CHKOK_OR_RETURN("OpenUnit");

	setIntegerParam(P_PicoConnected, 1);

	ok = ps3000aMaximumValue(ps.handle, &ps.max_value);
	CHKOK("MaximumValue");
	printf("max_value = %d\n", ps.max_value);
	printf("range = %d\n", ps.config.ch[0].range);

	ok = ps3000aGetAnalogueOffset(ps.handle, ps.config.ch[0].range, ps.config.ch[0].coupling, &ps.maximumVoltage, &ps.minimumVoltage);
	CHKOK("GetAnalogueOffset");
	printf("Minimum Voltage = %f\n", ps.minimumVoltage);
	printf("Maximum Voltage = %f\n", ps.maximumVoltage);

	ok = ps3000aGetMaxDownSampleRatio(ps.handle, ps.max_points, &ps.max_down_sample_ratio, PS3000A_RATIO_MODE_AVERAGE, 0);
	CHKOK("GetMaxDownSampleRatio");
	printf("Maximum downsample ratio = %u\n", ps.max_down_sample_ratio);

	
	return ok;
}

int PS3000A::ClosePS3000A() {
	PICO_STATUS ok;
	ok = ps3000aCloseUnit(ps.handle);
	CHKOK("Close");
	setIntegerParam(P_PicoConnected, 0);
	
	return 0;
}

int PS3000A::SetChannels() {
	epicsInt32 connected;
	getIntegerParam(P_PicoConnected, &connected);

	epicsInt32 max_points;
	getIntegerParam(P_MaxPoints, &max_points);

	// Channel A
	PS3000A_CHANNEL channel_A = PS3000A_CHANNEL(PS3000A_CHANNEL_A);
	epicsInt32 range_A;
	getIntegerParam(P_ChannelRangeA, &range_A);
	memset(pData_[0], 0, sizeof(epicsFloat64) * max_points);
	ps.config.ch[0].range = (PS3000A_RANGE) range_A;
	ps.config.ch[0].range_v = input_ranges[ps.config.ch[0].range];
	printf("Set channel %d: Range %d\n", 0, range_A);

	// Channel B
	PS3000A_CHANNEL channel_B = PS3000A_CHANNEL(PS3000A_CHANNEL_B);
	epicsInt32 range_B;
	getIntegerParam(P_ChannelRangeB, &range_B);
	memset(pData_[1], 0, sizeof(epicsFloat64) * max_points);
	ps.config.ch[1].range = (PS3000A_RANGE) range_B;
	ps.config.ch[1].range_v = input_ranges[ps.config.ch[1].range];
	printf("Set channel %d: Range %d\n", 1, range_B);

	int ok;
	if (connected != 0) {
		ok = ps3000aSetChannel(ps.handle, channel_A, 1, PS3000A_DC, (PS3000A_RANGE) range_A, 0);
		CHKOK("SetChannel");
		ok = ps3000aSetChannel(ps.handle, channel_B, 1, PS3000A_DC, (PS3000A_RANGE) range_B, 0);
		CHKOK("SetChannel");
	}
	
	return 0;
}

int32_t PS3000A::adc_to_uv(int32_t adc, int ch) {
	return ((float)adc * 1000. * ps.config.ch[ch].range_v) / ps.max_value;
}

int16_t PS3000A::mv_to_adc(int16_t mv, int ch) {
	return (mv * ps.max_value) / ps.config.ch[ch].range_v;
}

static const char *pico_info_strings[] = {
	"driver version",
	"usb version",
	"hardware version",
	"variant info",
	"batch and serial",
	"calibration date",
	"kernel version",
	"digital hardware version",
	"analog hardware version",
	"firmware version 1",
	"firmware version 2",
	"mac address",
	"shadow cal",
	"ipp version",
	"driver path",
	"firmware version 3",
	NULL
};

void PS3000A::PrintUnitInfo() {
	char string[BUFSIZ];
	int16_t string_length = BUFSIZ;
	int16_t required_size = 0;
	PICO_INFO info = 0;

	printf("------- Unit info -------\n");
	for (info = PICO_DRIVER_VERSION; info < PICO_FIRMWARE_VERSION_2;
	    ++info) {
		ps3000aGetUnitInfo(ps.handle, (int8_t *)&string[0],
		    string_length, &required_size, info);
		printf("%s: %*s\n", pico_info_strings[info], required_size,
		    string);
	}
	printf("----- End Unit info -----\n");
}

int PS3000A::SetTimeBase() {
	PICO_STATUS ok;
	epicsInt32 max_points;
	epicsInt32 sample_frequency;
	epicsInt32 time_base = 1;
	epicsInt32 max_samples = 0;
	epicsInt32 segment_index = 0;
	float time_interval_ns = 0;
	double full_time_ns;
	epicsInt32 connected;

	getIntegerParam(P_PicoConnected, &connected);
	if (connected == 0) return PICO_INTERFACE_NOT_CONNECTED;

	getIntegerParam(P_MaxPoints, &max_points);
	printf("Request Time Base = %d\n", time_base);
	ok = ps3000aGetTimebase2(ps.handle, time_base, max_points, &time_interval_ns, 0, &max_samples, segment_index);
	CHKOK("GetTimebase2");
	
	ps.time_base = time_base;
	printf("Maximum samples (regarding buffer capacity) = %d\n", max_samples);

	full_time_ns = max_points * time_interval_ns;
	setIntegerParam(P_SampleLength, full_time_ns);
	printf("Full time = %f ns\n", full_time_ns);

	printf("Sampling Interval (ns) = %f\n", time_interval_ns);
	setDoubleParam(P_SamplingInterval, time_interval_ns);
	ps.time_interval_ns = time_interval_ns;

	sample_frequency = PS3000A_FREQUENCY / time_interval_ns;
	printf("Sample frequency = %d Hz\n", sample_frequency);
	setIntegerParam(P_SampleFrequency, sample_frequency);
	printf("Samples needed = %d\n", max_points);
	
	return ok;
}

int PS3000A::SetDataBuffer() {
	PICO_STATUS ok;
	epicsInt32 max_points;
	PS3000A_RATIO_MODE mode = PS3000A_RATIO_MODE_NONE;

    getIntegerParam(P_MaxPoints, &max_points);
	ok = ps3000aSetDataBuffer(ps.handle, (PS3000A_CHANNEL) 0, data_buffer[0], max_points, 0, mode);
	ok = ps3000aSetDataBuffer(ps.handle, (PS3000A_CHANNEL) 1, data_buffer[1], max_points, 0, mode);
	CHKOK("SetDataBuffer");

	return 0;
}

int PS3000A::SetupTrigger() {
	PICO_STATUS ok = 0;
	epicsInt32 connected;
	getIntegerParam(P_PicoConnected, &connected);
	if (connected == 1) {
		ok = ps3000aSetSimpleTrigger(ps.handle, 1, PS3000A_EXTERNAL, 16000, PS3000A_RISING, 0, 0);
		CHKOK("SetSimpleTrigger");
	}
	
	return ok;
}

void PS3000A::ConnectPicoScope() {
	epicsInt32 connect, connected;
	getIntegerParam(P_PicoConnect, &connect);
	getIntegerParam(P_PicoConnected, &connected);
	printf("PICO connectPicoScope connect = %d\n", connect);
	if (connect == 0 && connected == 1) {
		printf("PICO Disconnecting...\n");
		ClosePS3000A();
		setIntegerParam(P_PicoConnected, 0);
	} else if (connected == 0 && connect == 1) {
		printf("PICO Connecting...\n");
		if(OpenPS3000A() != 0) return;
		SetChannels();
		PrintUnitInfo();
		SetTimeBase();
		SetTimeBaseArray();
		SetDataBuffer();
		SetupTrigger();
	}
}

int PS3000A::SetRangeChannel(int ch, epicsInt32 range) {
	epicsInt32 connected;
	getIntegerParam(P_PicoConnected, &connected);

	if (ch == 0) {
		// Channel A
		PS3000A_CHANNEL channel_A = PS3000A_CHANNEL(PS3000A_CHANNEL_A);
		setIntegerParam(P_ChannelRangeA, range);
		ps.config.ch[0].range = (PS3000A_RANGE) range;
		ps.config.ch[0].range_v = input_ranges[ps.config.ch[0].range];
		printf("Set channel A: Range %d\n", range);
		int ok;
		if (connected != 0) {
			ok = ps3000aSetChannel(ps.handle, channel_A, 1, PS3000A_DC, (PS3000A_RANGE) range, 0);
			CHKOK("SetChannel");
		}
	} else if (ch == 1) {
		// Channel A
		PS3000A_CHANNEL channel_B = PS3000A_CHANNEL(PS3000A_CHANNEL_B);
		setIntegerParam(P_ChannelRangeB, range);
		ps.config.ch[1].range = (PS3000A_RANGE) range;
		ps.config.ch[1].range_v = input_ranges[ps.config.ch[1].range];
		printf("Set channel B: Range %d\n", range);
		int ok;
		if (connected != 0) {
			ok = ps3000aSetChannel(ps.handle, channel_B, 1, PS3000A_DC, (PS3000A_RANGE) range, 0);
			CHKOK("SetChannel");
		}
	} else { return -1;}

	
	return 0;
}

/** Called when asyn clients call pasynInt32->write().
  * This function sends a signal to the simTask thread if the value of P_Run has changed.
  * For all parameters it sets the value in the parameter library and calls any registered callbacks..
  * \param[in] pasynUser pasynUser structure that encodes the reason and address.
  * \param[in] value Value to write. */
asynStatus PS3000A::writeInt32(asynUser *pasynUser, epicsInt32 value) {
    int function = pasynUser->reason;
    asynStatus status = asynSuccess;
    const char *paramName;
    const char* functionName = "writeInt32";

    /* Set the parameter in the parameter library. */
    status = (asynStatus) setIntegerParam(function, value);

    /* Fetch the parameter string name for possible use in debugging */
    getParamName(function, &paramName);
    if (function == P_Run) {
        /* If run was set then wake up the simulation task */
        if (value) epicsEventSignal(eventId_);
    } else if (function == P_PicoConnect) {
		ConnectPicoScope();
    } else if (function == P_ChannelRangeA) {
		SetRangeChannel(0, value);
    } else if (function == P_ChannelRangeB) {
		SetRangeChannel(1, value);
    } else {}

    /* Do callbacks so higher layers see any changes */
    status = (asynStatus) callParamCallbacks();
    if (status)
        epicsSnprintf(pasynUser->errorMessage, pasynUser->errorMessageSize, "%s:%s: status=%d, function=%d, name=%s, value=%d", driverName, functionName, status, function, paramName, value);
    else
        asynPrint(pasynUser, ASYN_TRACEIO_DRIVER, "%s:%s: function=%d, name=%s, value=%d\n", driverName, functionName, function, paramName, value);
    return status;
}

/** Called when asyn clients call pasynFloat64Array->read().
  * Returns the value of the P_Waveform or P_TimeBase arrays.  
  * \param[in] pasynUser pasynUser structure that encodes the reason and address.
  * \param[in] value Pointer to the array to read.
  * \param[in] nElements Number of elements to read.
  * \param[out] nIn Number of elements actually read. */
asynStatus PS3000A::readFloat64Array(asynUser *pasynUser, epicsFloat64 *value, size_t nElements, size_t *nIn) {
    int function = pasynUser->reason;
    size_t ncopy;
    epicsInt32 itemp;
    asynStatus status = asynSuccess;
    epicsTimeStamp timeStamp;
    const char *functionName = "readFloat64Array";
    getTimeStamp(&timeStamp);
    pasynUser->timestamp = timeStamp;
    getIntegerParam(P_SampleLength, &itemp);
    ncopy = itemp;
    if (nElements < ncopy) ncopy = nElements;
    if (function == P_WaveformA) {
		memcpy(value, pData_[0], ncopy*sizeof(epicsFloat64));
		*nIn = ncopy;
	} else if (function == P_WaveformB) {
		memcpy(value, pData_[1], ncopy*sizeof(epicsFloat64));
		*nIn = ncopy;
	} else if (function == P_TimeBase) {
        memcpy(value, pTimeBase_, ncopy*sizeof(epicsFloat64));
        *nIn = ncopy;
    } else {}

    if (status) epicsSnprintf(pasynUser->errorMessage, pasynUser->errorMessageSize, "%s:%s: status=%d, function=%d", driverName, functionName, status, function);
    else asynPrint(pasynUser, ASYN_TRACEIO_DRIVER, "%s:%s: function=%d\n", driverName, functionName, function);

    return status;
}

/* Configuration routine.  Called directly, or from the iocsh function below */
extern "C" {
	/** EPICS iocsh callable function to call constructor for the PS3000A class.
	* \param[in] portName The name of the asyn port driver to be created.
	* \param[in] maxPoints The maximum  number of points in the volt and time arrays */
	int PS3000AConfigure(const char *portName, int maxPoints) {
		new PS3000A(portName, maxPoints);
		return(asynSuccess);
	}

	/* EPICS iocsh shell commands */
	static const iocshArg initArg0 = { "portName",iocshArgString};
	static const iocshArg initArg1 = { "max points",iocshArgInt};
	static const iocshArg * const initArgs[] = {&initArg0, &initArg1};
	static const iocshFuncDef initFuncDef = {"PS3000AConfigure",2,initArgs};
	static void initCallFunc(const iocshArgBuf *args) {
		PS3000AConfigure(args[0].sval, args[1].ival);
	}

	void PS3000ARegister(void) {
		iocshRegister(&initFuncDef,initCallFunc);
	}

	epicsExportRegistrar(PS3000ARegister);
}
