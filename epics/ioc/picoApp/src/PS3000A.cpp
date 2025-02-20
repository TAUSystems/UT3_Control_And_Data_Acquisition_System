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

#define NUM_DIVISIONS 10     /* Number of scope divisions in X and Y */
#define MIN_UPDATE_TIME 0.02 /* Minimum update time, to prevent CPU saturation */
#define N_CH 2
#define PS3000A_FREQUENCY 1000000000

#define MAX_ENUM_STRING_SIZE 20
static int allVoltsPerDivSelections[NUM_VERT_SELECTIONS]={5,10,20,50,100,200,500,1000,2000,5000,10000,20000};

static const char *driverName="PS3000A";
void run_task(void *drvPvt);

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
    int i, ch;
    asynStatus status;
    const char *functionName = "PS3000A";

    /* Make sure maxPoints is positive */
    if (maxPoints < 1) maxPoints = 1000;

    /* Allocate the output waveform array */
    pData_[0] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));
    pData_[1] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));
    pData_[2] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));
    pData_[3] = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));

    /* Allocate the waveform array (pico scope delivers int16_t array */
    data_buffer[0] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */
    data_buffer[1] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */
    data_buffer[2] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */
    data_buffer[3] = (int16_t *)calloc(maxPoints, sizeof(int16_t)); /* uV */

    /* Allocate the time base array */
    pTimeBase_ = (epicsFloat64 *)calloc(maxPoints, sizeof(epicsFloat64));

    eventId_ = epicsEventCreate(epicsEventEmpty);
    createParam(P_RunString, asynParamInt32, &P_Run);
    createParam(P_MaxPointsString, asynParamInt32,&P_MaxPoints);
    createParam(P_TimePerDivString, asynParamFloat64, &P_TimePerDiv);
    createParam(P_FullTimeString, asynParamFloat64, &P_FullTime);
    createParam(P_TimePerDivSelectString, asynParamInt32, &P_TimePerDivSelect);
    createParam(P_VoltsPerDivStringA, asynParamFloat64, &P_VoltsPerDiv[0]);
    createParam(P_VoltsPerDivStringB, asynParamFloat64, &P_VoltsPerDiv[1]);
    createParam(P_VoltsPerDivStringC, asynParamFloat64, &P_VoltsPerDiv[2]);
    createParam(P_VoltsPerDivStringD, asynParamFloat64, &P_VoltsPerDiv[3]);
    createParam(P_VoltsPerDivSelectStringA, asynParamInt32, &P_VoltsPerDivSelect[0]);
    createParam(P_VoltsPerDivSelectStringB, asynParamInt32, &P_VoltsPerDivSelect[1]);
    createParam(P_VoltsPerDivSelectStringC, asynParamInt32, &P_VoltsPerDivSelect[2]);
    createParam(P_VoltsPerDivSelectStringD, asynParamInt32, &P_VoltsPerDivSelect[3]);
    createParam(P_VoltOffsetStringA, asynParamFloat64, &P_VoltOffset[0]);
    createParam(P_VoltOffsetStringB, asynParamFloat64, &P_VoltOffset[1]);
    createParam(P_VoltOffsetStringC, asynParamFloat64, &P_VoltOffset[2]);
    createParam(P_VoltOffsetStringD, asynParamFloat64, &P_VoltOffset[3]);
    createParam(P_TriggerDelayString, asynParamFloat64, &P_TriggerDelay);
    createParam(P_NoiseAmplitudeString, asynParamFloat64, &P_NoiseAmplitude);
    createParam(P_UpdateTimeString, asynParamFloat64, &P_UpdateTime);
    createParam(P_Waveform_StringA, asynParamFloat64Array, &P_Waveform[0]);
    createParam(P_Waveform_StringB, asynParamFloat64Array, &P_Waveform[1]);
    createParam(P_Waveform_StringC, asynParamFloat64Array, &P_Waveform[2]);
    createParam(P_Waveform_StringD, asynParamFloat64Array, &P_Waveform[3]);
    createParam(P_TimeBaseString, asynParamFloat64Array, &P_TimeBase);
    createParam(P_MinValueString, asynParamFloat64, &P_MinValue);
    createParam(P_MaxValueString, asynParamFloat64, &P_MaxValue);
    createParam(P_MeanValueString, asynParamFloat64, &P_MeanValue);

    createParam(P_PicoStatusString, asynParamInt32, &P_PicoStatus);
    createParam(P_PicoConnectString, asynParamInt32, &P_PicoConnect);
    createParam(P_PicoConnectedString, asynParamInt32, &P_PicoConnected);
    createParam(P_max_samples_string, asynParamInt32, &P_max_samples);
    createParam(P_segment_index_string, asynParamInt32, &P_segment_index);
    createParam(P_downsampled_frequency_string, asynParamInt32, &P_downsampled_frequency);
    createParam(P_sample_frequency_string, asynParamInt32, &P_sample_frequency);
    createParam(P_sample_length_string, asynParamInt32, &P_sample_length);
    createParam(P_time_interval_ns_string, asynParamFloat64, &P_time_interval_ns);
    createParam(P_down_sample_ratio_string, asynParamInt32, &P_down_sample_ratio);
    createParam(P_ch_A_coupling_string, asynParamInt32, &P_ch_coupling[0]);
    createParam(P_ch_A_enabled_string, asynParamInt32, &P_ch_enabled[0]);
    createParam(P_ch_A_offset_string, asynParamFloat64, &P_ch_offset[0]);
    createParam(P_ch_A_range_string, asynParamInt32, &P_ch_range[0]);
    createParam(P_ch_A_direction_string, asynParamInt32, &P_ch_direction[0]);
    createParam(P_ch_A_condition_string, asynParamInt32, &P_ch_condition[0]);
    createParam(P_ch_A_threshold_string, asynParamFloat64, &P_ch_threshold[0]);
    createParam(P_ch_A_overflow_string, asynParamInt32, &P_ch_overflow[0]);

    createParam(P_ch_B_coupling_string, asynParamInt32, &P_ch_coupling[1]);
    createParam(P_ch_B_enabled_string, asynParamInt32, &P_ch_enabled[1]);
    createParam(P_ch_B_offset_string, asynParamFloat64, &P_ch_offset[1]);
    createParam(P_ch_B_range_string, asynParamInt32, &P_ch_range[1]);
    createParam(P_ch_B_direction_string, asynParamInt32, &P_ch_direction[1]);
    createParam(P_ch_B_condition_string, asynParamInt32, &P_ch_condition[1]);
    createParam(P_ch_B_threshold_string, asynParamFloat64, &P_ch_threshold[1]);
    createParam(P_ch_B_overflow_string, asynParamInt32, &P_ch_overflow[1]);

    createParam(P_ch_C_coupling_string, asynParamInt32, &P_ch_coupling[2]);
    createParam(P_ch_C_enabled_string, asynParamInt32, &P_ch_enabled[2]);
    createParam(P_ch_C_offset_string, asynParamFloat64, &P_ch_offset[2]);
    createParam(P_ch_C_range_string, asynParamInt32, &P_ch_range[2]);
    createParam(P_ch_C_direction_string, asynParamInt32, &P_ch_direction[2]);
    createParam(P_ch_C_condition_string, asynParamInt32, &P_ch_condition[2]);
    createParam(P_ch_C_threshold_string, asynParamFloat64, &P_ch_threshold[2]);
    createParam(P_ch_C_overflow_string, asynParamInt32, &P_ch_overflow[2]);

    createParam(P_ch_D_coupling_string, asynParamInt32, &P_ch_coupling[3]);
    createParam(P_ch_D_enabled_string, asynParamInt32, &P_ch_enabled[3]);
    createParam(P_ch_D_offset_string, asynParamFloat64, &P_ch_offset[3]);
    createParam(P_ch_D_range_string, asynParamInt32, &P_ch_range[3]);
    createParam(P_ch_D_direction_string, asynParamInt32, &P_ch_direction[3]);
    createParam(P_ch_D_condition_string, asynParamInt32, &P_ch_condition[3]);
    createParam(P_ch_D_threshold_string, asynParamFloat64, &P_ch_threshold[3]);
    createParam(P_ch_D_overflow_string, asynParamInt32, &P_ch_overflow[3]);

    createParam(P_sig_offset_string, asynParamInt32, &P_sig_offset);
    createParam(P_sig_pktopk_string, asynParamFloat64, &P_sig_pktopk);
    createParam(P_sig_wavetype_string, asynParamInt32, &P_sig_wavetype);
    createParam(P_sig_frequency_string, asynParamFloat64, &P_sig_frequency);
    createParam(P_sig_trigger_source_string, asynParamInt32,
	&P_sig_trigger_source);

    createParam(P_time_base_lopr_string, asynParamInt32, &P_time_base_lopr);
    createParam(P_time_base_hopr_string, asynParamInt32, &P_time_base_hopr);
    createParam(P_time_base_nelm_string, asynParamInt32, &P_time_base_nelm);

    createParam(P_trigger_source_string, asynParamInt32, &P_trigger_source);

    /* init volts per div values */
    for (i = 0; i < NUM_VERT_SELECTIONS; i++) {
        voltsPerDivStrings_[i] = (char *)calloc(MAX_ENUM_STRING_SIZE, sizeof(char));
        voltsPerDivSeverities_[i] = 0;
        epicsSnprintf(voltsPerDivStrings_[i], MAX_ENUM_STRING_SIZE, "%g", allVoltsPerDivSelections[i] / 1000.);
        // The values are in mV
        voltsPerDivValues_[i] = (int)(allVoltsPerDivSelections[i]);
    }

    /* Set the initial values of some parameters */
    setIntegerParam(P_PicoStatus,        0);
    setIntegerParam(P_PicoConnected,     0);
    setIntegerParam(P_MaxPoints,         maxPoints);
    ps.max_points = maxPoints;
    setIntegerParam(P_Run,               0);

    ps.max_value = 32512;

    /* Initial values for all channel parameters */
    for (ch = 0; ch < 4; ++ch) {
	    setDoubleParam (P_VoltsPerDiv[ch],       1.0);
	    setIntegerParam(P_VoltsPerDivSelect[ch], 100);
	    setDoubleParam (P_VoltOffset[ch],        0.0);
	    setIntegerParam(P_ch_coupling[ch],	PS3000A_DC);
	    setIntegerParam(P_ch_enabled[ch],	0);
	    setDoubleParam (P_ch_offset[ch],	0);
	    setIntegerParam(P_ch_range[ch],	PS3000A_500MV);
	    ps.config.ch[ch].range = PS3000A_500MV;
	    ps.config.ch[ch].range_v = input_ranges[ps.config.ch[ch].range];
	    setDoubleParam (P_ch_threshold[ch],	mv_to_adc(-10, ch));
	    setIntegerParam(P_ch_condition[ch],	PS3000A_CONDITION_DONT_CARE);
	    setIntegerParam(P_ch_direction[ch],	PS3000A_FALLING);
    }

    /* Enable trigger on channel A */
    setIntegerParam(P_ch_enabled  [0],	1                     ); /* Enable Channel A*/
    setIntegerParam(P_ch_condition[0],	PS3000A_CONDITION_TRUE); /* Set Trigger Condition, see API [enPS3000ATriggerState]*/

    setIntegerParam(P_down_sample_ratio, 1);					 /* No down sampling */
    setIntegerParam(P_time_base_lopr, 0);                        /* Minimum operation value (0), please see "Sampling Interval Formula" in 3000A API docs */
    setIntegerParam(P_time_base_hopr, 9); 					  	 /* Maximum operation value (9) */
    setIntegerParam(P_time_base_nelm, maxPoints); 			    

    setDoubleParam (P_TriggerDelay,      0.0);					 /* Trigger delay in sampling periods (NOT nanoseconds) */
    setDoubleParam (P_FullTime,         2000);					 /* Sampling duration in nanoseconds */
    setDoubleParam (P_TimePerDiv,        200);						 /* Time per division in nanoseconds */
    setDoubleParam (P_UpdateTime,        0.5);
    setDoubleParam (P_NoiseAmplitude,    0.1);
    setDoubleParam (P_MinValue,          0.0);
    setDoubleParam (P_MaxValue,          0.0);
    setDoubleParam (P_MeanValue,         0.0);

    setIntegerParam(P_max_samples,	maxPoints);					/* Maximum number of sampling points */
    setIntegerParam(P_segment_index,	0);
    setIntegerParam(P_downsampled_frequency, 1000000000);
    setIntegerParam(P_sample_frequency, 1000000000);
    setIntegerParam(P_sample_length,	maxPoints);    		    /* Number of sampling points*/
    set_time_base_array();

    setDoubleParam (P_time_interval_ns,	0);						 /* Sampling interval in nanoseconds */

    setIntegerParam(P_trigger_source,	PS3000A_CHANNEL_A);      /* Trigger Source on Channel A*/ // FIXME: This should be on EXTERNAL

	// FIXME: Should turn off signal generator
    setIntegerParam(P_sig_offset,	0);
    setDoubleParam (P_sig_pktopk,	1.0); /* Volt */
    setIntegerParam(P_sig_wavetype,	PS3000A_SINE);
    setDoubleParam (P_sig_frequency,	1e6); /* Hz */
    setIntegerParam(P_sig_trigger_source, PS3000A_SIGGEN_NONE);

    /* Create the thread that runs the waveforms acq in the background */
    status = (asynStatus)(epicsThreadCreate("PS3000ATask",
                          epicsThreadPriorityMedium,
                          epicsThreadGetStackSize(epicsThreadStackMedium),
                          (EPICSTHREADFUNC)::run_task,
                          this) == NULL);

    if (status) {
        printf("%s:%s: epicsThreadCreate failure\n", driverName, functionName);
        return;
    }

}

void PS3000A::set_time_base_array() {
	int i;
	epicsInt32 max_points = 0;
	getIntegerParam(P_MaxPoints, &max_points);

	/* Set the time base array */
	for (i = 0; i < max_points; ++i) {
		pTimeBase_[i] = (double)i / (max_points - 1) * NUM_DIVISIONS;
	}

        doCallbacksFloat64Array(pTimeBase_, max_points,
	    P_TimeBase, 0);
}

void run_task(void *drvPvt) {
    PS3000A *pPvt = (PS3000A *)drvPvt;
    pPvt->run_task();
}

void pico_block_ready(int16_t handle, PICO_STATUS ok, void *p_parameter) {
	struct BlockInfo *info = (struct BlockInfo *)p_parameter;

	if (ok != PICO_CANCELLED) {
		info->ready = 1;
	}
}

void PS3000A::run_task() {
	epicsInt32 run;
	double updateTime;

	lock();

	while(1)
	{
		getDoubleParam(P_UpdateTime, &updateTime);
		getIntegerParam(P_Run, &run);

		unlock();

		if (run) epicsEventWaitWithTimeout(eventId_, updateTime);
		else     (void) epicsEventWait(eventId_);

		lock();

        	getIntegerParam(P_Run, &run);
        	if (!run) continue;

		pico_run_block();
	}
}

int PS3000A::pico_run_block() {
	PICO_STATUS ok;

	epicsInt32 sample_length;
	epicsInt32 max_points;
	epicsInt32 segment_index;
	epicsInt32 down_sample_ratio;
	double volts_per_div[4], volt_offset[4];
	double min_value, max_value, mean_value;

	getIntegerParam(P_MaxPoints, &max_points);
	getIntegerParam(P_sample_length, &sample_length);
	getIntegerParam(P_segment_index, &segment_index);
	getIntegerParam(P_down_sample_ratio, &down_sample_ratio);
        getDoubleParam (P_VoltsPerDiv[0], &volts_per_div[0]);
        getDoubleParam (P_VoltsPerDiv[1], &volts_per_div[1]);
        getDoubleParam (P_VoltsPerDiv[2], &volts_per_div[2]);
        getDoubleParam (P_VoltsPerDiv[3], &volts_per_div[3]);
        getDoubleParam (P_VoltOffset[0], &volt_offset[0]);
        getDoubleParam (P_VoltOffset[1], &volt_offset[1]);
        getDoubleParam (P_VoltOffset[2], &volt_offset[2]);
        getDoubleParam (P_VoltOffset[3], &volt_offset[3]);

	/*printf("sample length = %d\n", sample_length);*/

	uint32_t pre_ds_sample_length = sample_length * down_sample_ratio;

	/*
	 * Trigger time is at 50 % of the screen
	 */
	float trigger_fraction = 0.5;
	int32_t pre_trigger = pre_ds_sample_length * (1. - trigger_fraction);
	int32_t post_trigger = pre_ds_sample_length * trigger_fraction;
	int32_t time_indisposed_ms = 0;
	ps3000aBlockReady callback_block_ready = pico_block_ready;
	struct BlockInfo block_info;
	block_info.ready = 0;
	void *p_parameter = (void *)&block_info;
	int cnt = 0;
	const int trigger_timeout = 1000; /* ms */
	PS3000A_RATIO_MODE down_sample_ratio_mode = PS3000A_RATIO_MODE_AVERAGE;
	uint32_t n_samples = sample_length;
	uint32_t start_index = 0;

	/*printf("pico_run_block\n");*/

	/*printf("pre_ds_sample_length = %u\n", pre_ds_sample_length);
	printf("pre_trigger = %d\n", pre_trigger);
	printf("post_trigger = %d\n", post_trigger);*/
	/*printf("ps.time_interval_ns = %f\n", ps.time_interval_ns);
	printf("ps.time_base = %u\n", (uint32_t)ps.time_base);*/
	ok = ps3000aRunBlock(ps.handle, pre_trigger, post_trigger,
	    ps.time_base, 0, &time_indisposed_ms,
	    segment_index, callback_block_ready, p_parameter);
	CHKOK("RunBlock");

	/*printf("Waiting for trigger...\n");*/

	cnt = 0;
	while (block_info.ready == 0) {
		epicsThreadSleep(1e-3);
		cnt++;
		if (cnt == trigger_timeout) {
			printf("No trigger in %d ms\n", trigger_timeout);
			return 44;
		}
	}

	/*printf("Triggered.\n");*/

	min_value = 1e6;
	max_value = -1e6;
	mean_value = 0;
	if (block_info.ready == 1) {
		int i;
		uint32_t ch;
		double val;
		int64_t time;
		PS3000A_TIME_UNITS time_units;
		int16_t overflow = 0;

		/*printf("Retrieving data...\n");*/
		ok = ps3000aGetValues(ps.handle, start_index,
		    &n_samples, down_sample_ratio, down_sample_ratio_mode,
		    segment_index, &overflow);
		/*printf("%d samples\n", n_samples);
		printf("%d overflow\n", overflow);*/
		CHKOK("GetValues");

		ok = ps3000aGetTriggerTimeOffset64(ps.handle, &time,
		    &time_units, segment_index);
		CHKOK("GetTriggerTimeOffset");

		// double sampled_time_ns = n_samples * ps.time_interval_ns * down_sample_ratio;
		/*printf("%f sampled_time_ns\n", sampled_time_ns);*/

		/*printf("Trigger time = %ld %d.\n", time, time_units);*/

		for (ch = 0; ch < 4; ++ch) {
			epicsInt32 enabled;
			double offset = volt_offset[ch] +
			    volts_per_div[ch] * NUM_DIVISIONS / 2;

			getIntegerParam(P_ch_enabled[ch], &enabled);
			if (enabled == 0) continue;

			/*printf("Got block data with %d samples\n", n_samples);
			*/

			for (i = start_index; i < max_points; ++i) {
				int bin = i * (double)n_samples /
				    (double)max_points;
				val = adc_to_uv(data_buffer[ch][bin], ch) / 1e6;
				if (val < min_value) min_value = val;
				if (val > max_value) max_value = val;
				pData_[ch][i] = (offset + val)
				    / volts_per_div[ch];
			}
			setDoubleParam(P_MinValue, min_value);
			setDoubleParam(P_MaxValue, max_value);
			setDoubleParam(P_MeanValue, mean_value);
			mean_value = mean_value / n_samples;
        		doCallbacksFloat64Array(pData_[ch], max_points,
			    P_Waveform[ch], 0);
			setIntegerParam(P_ch_overflow[ch],
			    (overflow >> ch) & 1);
		}

        	callParamCallbacks();
	} else {
		printf("What??\n");
	}

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
    }
    else if (function == P_VoltsPerDivSelect[0]) {
        setVoltsPerDiv(0);
    }
    else if (function == P_VoltsPerDivSelect[1]) {
        setVoltsPerDiv(1);
    }
    else if (function == P_VoltsPerDivSelect[2]) {
        setVoltsPerDiv(2);
    }
    else if (function == P_VoltsPerDivSelect[3]) {
        setVoltsPerDiv(3);
    }
    else if (function == P_TimePerDivSelect) {
        setTimePerDiv();
    }
    else if (function == P_PicoConnect) {
		ConnectPicoScope();
    }
    else if (function == P_trigger_source) {
	    set_trigger_source();
    }
    else if (function == P_ch_coupling[0]
	|| function == P_ch_enabled[0]
	|| function == P_ch_range[0]) {
	    set_channel(0);
	    set_time_base();
	    setup_trigger();
    }
    else if (function == P_ch_coupling[1]
	|| function == P_ch_enabled[1]
	|| function == P_ch_range[1]) {
	    set_channel(1);
	    set_time_base();
	    setup_trigger();
    }
    else if (function == P_ch_coupling[2]
	|| function == P_ch_enabled[2]
	|| function == P_ch_range[2]) {
	    set_channel(2);
	    set_time_base();
	    setup_trigger();
    }
    else if (function == P_ch_coupling[3]
	|| function == P_ch_enabled[3]
	|| function == P_ch_range[3]) {
	    set_channel(3);
	    set_time_base();
	    setup_trigger();
    }
    else if (function == P_sample_frequency) {
	    set_time_base();
    }
    else if (function == P_ch_direction[0]
	  || function == P_ch_direction[1]
	  || function == P_ch_direction[2]
	  || function == P_ch_direction[3]) {
	    setup_trigger();
    }
    else if (function == P_ch_condition[0]
	  || function == P_ch_condition[1]
	  || function == P_ch_condition[2]
	  || function == P_ch_condition[3]) {
	    setup_trigger();
    }
    else if (function == P_sig_offset
	  || function == P_sig_wavetype
	  || function == P_sig_trigger_source) {
	    set_signal_generator();
    }
    else {
        /* All other parameters just get set in parameter list, no need to
         * act on them here */
    }

    /* Do callbacks so higher layers see any changes */
    status = (asynStatus) callParamCallbacks();

    if (status)
        epicsSnprintf(pasynUser->errorMessage, pasynUser->errorMessageSize,
                  "%s:%s: status=%d, function=%d, name=%s, value=%d",
                  driverName, functionName, status, function, paramName, value);
    else
        asynPrint(pasynUser, ASYN_TRACEIO_DRIVER,
              "%s:%s: function=%d, name=%s, value=%d\n",
              driverName, functionName, function, paramName, value);
    return status;
}

/** Called when asyn clients call pasynFloat64->write().
  * This function sends a signal to the simTask thread if the value of P_UpdateTime has changed.
  * For all  parameters it  sets the value in the parameter library and calls any registered callbacks.
  * \param[in] pasynUser pasynUser structure that encodes the reason and address.
  * \param[in] value Value to write. */
asynStatus PS3000A::writeFloat64(asynUser *pasynUser, epicsFloat64 value) {
    int function = pasynUser->reason;
    asynStatus status = asynSuccess;
    epicsInt32 run;
    const char *paramName;
    const char* functionName = "writeFloat64";

    /* Set the parameter in the parameter library. */
    status = (asynStatus) setDoubleParam(function, value);

    /* Fetch the parameter string name for possible use in debugging */
    getParamName(function, &paramName);

    if (function == P_UpdateTime) {
        /* Make sure the update time is valid. If not change it and put back in parameter library */
        if (value < MIN_UPDATE_TIME) {
            asynPrint(pasynUser, ASYN_TRACE_WARNING,
                "%s:%s: warning, update time too small, changed from %f to %f\n",
                driverName, functionName, value, MIN_UPDATE_TIME);
            value = MIN_UPDATE_TIME;
            setDoubleParam(P_UpdateTime, value);
        }
        /* If the update time has changed and we are running then wake up the simulation task */
        getIntegerParam(P_Run, &run);
        if (run) epicsEventSignal(eventId_);
    }
    else if (function == P_ch_threshold[0]) {
	    set_trigger(0);
    }
    else if (function == P_ch_threshold[1]) {
	    set_trigger(1);
    }
    else if (function == P_ch_threshold[2]) {
	    set_trigger(2);
    }
    else if (function == P_ch_threshold[3]) {
	    set_trigger(3);
    }
    else if (function == P_sig_frequency
	  || function == P_sig_pktopk) {
	    set_signal_generator();
    }
    else {
        /* All other parameters just get set in parameter list, no need to
         * act on them here */
    }

    /* Do callbacks so higher layers see any changes */
    status = (asynStatus) callParamCallbacks();

    if (status)
        epicsSnprintf(pasynUser->errorMessage, pasynUser->errorMessageSize,
                  "%s:%s: status=%d, function=%d, name=%s, value=%f",
                  driverName, functionName, status, function, paramName, value);
    else
        asynPrint(pasynUser, ASYN_TRACEIO_DRIVER,
              "%s:%s: function=%d, name=%s, value=%f\n",
              driverName, functionName, function, paramName, value);
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
    int ch;
    epicsInt32 itemp;
    asynStatus status = asynSuccess;
    epicsTimeStamp timeStamp;
    epicsInt32 enabled;

    const char *functionName = "readFloat64Array";

    getTimeStamp(&timeStamp);
    pasynUser->timestamp = timeStamp;
    getIntegerParam(P_sample_length, &itemp);
    ncopy = itemp;

    if (nElements < ncopy) ncopy = nElements;
    for (ch = 0; ch < 4; ++ch) {
	    if (function == P_Waveform[ch]) {
		    getIntegerParam(P_ch_enabled[ch], &enabled);
		    if (enabled == 1) {
			    memcpy(value, pData_[ch],
				ncopy*sizeof(epicsFloat64));
			    *nIn = ncopy;
		    } else {
			    *nIn = 0;
		    }
	    }
    }
    if (function == P_TimeBase) {
        memcpy(value, pTimeBase_, ncopy*sizeof(epicsFloat64));
        *nIn = ncopy;
    }
    if (status)
        epicsSnprintf(pasynUser->errorMessage, pasynUser->errorMessageSize,
                  "%s:%s: status=%d, function=%d",
                  driverName, functionName, status, function);
    else
        asynPrint(pasynUser, ASYN_TRACEIO_DRIVER,
              "%s:%s: function=%d\n",
              driverName, functionName, function);
    return status;
}

asynStatus PS3000A::readEnum(asynUser *pasynUser, char *strings[], int values[], int severities[], size_t nElements, size_t *nIn) {
    int function = pasynUser->reason;
    size_t i;

    if (function == P_VoltsPerDivSelect[0]) {
        for (i = 0; ((i < NUM_VERT_SELECTIONS) && (i < nElements)); i++) {
            if (strings[i]) free(strings[i]);
            strings[i] = epicsStrDup(voltsPerDivStrings_[i]);
            values[i] = voltsPerDivValues_[i];
            severities[i] = 0;
        }
    }
    else if (function == P_VoltsPerDivSelect[1]) {
        for (i = 0; ((i < NUM_VERT_SELECTIONS) && (i < nElements)); i++) {
            if (strings[i]) free(strings[i]);
            strings[i] = epicsStrDup(voltsPerDivStrings_[i]);
            values[i] = voltsPerDivValues_[i];
            severities[i] = 0;
        }
    }
    else if (function == P_VoltsPerDivSelect[2]) {
        for (i = 0; ((i < NUM_VERT_SELECTIONS) && (i < nElements)); i++) {
            if (strings[i]) free(strings[i]);
            strings[i] = epicsStrDup(voltsPerDivStrings_[i]);
            values[i] = voltsPerDivValues_[i];
            severities[i] = 0;
        }
    }
    else if (function == P_VoltsPerDivSelect[3]) {
        for (i = 0; ((i < NUM_VERT_SELECTIONS) && (i < nElements)); i++) {
            if (strings[i]) free(strings[i]);
            strings[i] = epicsStrDup(voltsPerDivStrings_[i]);
            values[i] = voltsPerDivValues_[i];
            severities[i] = 0;
        }
    }
    else {
        *nIn = 0;
        return asynError;
    }
    *nIn = i;
    return asynSuccess;
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

	ok = ps3000aGetAnalogueOffset(ps.handle, ps.config.ch[0].range,
	    ps.config.ch[0].coupling, &ps.maximumVoltage, &ps.minimumVoltage);
	CHKOK("GetAnalogueOffset");
	printf("Minimum Voltage = %f\n", ps.minimumVoltage);
	printf("Maximum Voltage = %f\n", ps.maximumVoltage);

	ok = ps3000aGetMaxDownSampleRatio(ps.handle, ps.max_points,
	    &ps.max_down_sample_ratio, PS3000A_RATIO_MODE_AVERAGE, 0);
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

int PS3000A::set_channel(int ch) {
	int ok;
	PS3000A_CHANNEL channel = PS3000A_CHANNEL(PS3000A_CHANNEL_A + ch);

	epicsInt32 enabled;
	epicsInt32 coupling;
	epicsInt32 range;
	epicsInt32 connected;
	epicsInt32 max_points;
	double analog_offset;

	getIntegerParam(P_PicoConnected, &connected);
	getIntegerParam(P_ch_enabled[ch], &enabled);
	getIntegerParam(P_ch_coupling[ch], &coupling);
	getIntegerParam(P_ch_range[ch], &range);
	getIntegerParam(P_MaxPoints, &max_points);
	getDoubleParam(P_ch_offset[ch], &analog_offset);

	memset(pData_[ch], 0, sizeof(epicsFloat64) * max_points);

    	ps.config.ch[ch].range = (PS3000A_RANGE)range;
	ps.config.ch[ch].range_v = input_ranges[ps.config.ch[ch].range];

	/*printf("Set channel %d: %d, %d, %d, %f\n", ch, enabled, coupling, range,
	    analog_offset);*/

	if (connected != 0) {
		ok = ps3000aSetChannel(ps.handle, channel, (int16_t)enabled,
		    (PS3000A_COUPLING)coupling, (PS3000A_RANGE)range,
		    (float)analog_offset);
		CHKOK("SetChannel");
	}

	return 0;
}

float PS3000A::s_to_ns(int32_t s) {
	return s * ps.time_interval_ns;
}

int32_t PS3000A::adc_to_uv(int32_t adc, int ch) {
	return ((float)adc * 1000. * ps.config.ch[ch].range_v) / ps.max_value;
}

int16_t PS3000A::mv_to_adc(int16_t mv, int ch) {
	return (mv * ps.max_value) / ps.config.ch[ch].range_v;
}

int PS3000A::set_trigger(int ch) {
	PICO_STATUS ok;

	PS3000A_TRIGGER_CHANNEL_PROPERTIES channelProperties[N_CH];
	int16_t nChannelProperties = 1;

	int32_t autoTriggerMilliseconds = 100;

	epicsFloat64 ch_thr;
	epicsInt32 connected;
	epicsInt32 enabled;
	epicsInt32 source;

	getIntegerParam(P_PicoConnected, &connected);
	getIntegerParam(P_ch_enabled[ch], &enabled);
	getIntegerParam(P_trigger_source, &source);
	getDoubleParam(P_ch_threshold[ch], &ch_thr);

	/*printf("ch_%d_threshold = %f\n", ch, ch_thr);*/

	int16_t thr = mv_to_adc(ch_thr, ch);

	/*printf("thr = %d\n", thr);*/

	channelProperties[0].thresholdUpper = thr;
	channelProperties[0].thresholdUpperHysteresis = 2 * 256;
	channelProperties[0].thresholdLower = thr;
	channelProperties[0].thresholdLowerHysteresis = 2 * 256;
	channelProperties[0].channel =
	    (PS3000A_CHANNEL)(PS3000A_CHANNEL_A + ch);
	channelProperties[0].thresholdMode = PS3000A_LEVEL;

	if (enabled == 1 && ch == source) {
		if (connected == 1) {
			ok = ps3000aSetTriggerChannelProperties(ps.handle,
			    channelProperties, nChannelProperties, 0,
			    autoTriggerMilliseconds);
			CHKOK("SetTriggerChannelProperties");
		} else {
			printf("SetTriggerChannelProperties: Not connected.\n");
		}
	}

	return 0;
}

int PS3000A::set_sig_trigger_source() {
	int ch;
	epicsInt32 source;
	getIntegerParam(P_trigger_source, &source);

	for (ch = 0; ch < 4; ++ch) {
		PS3000A_TRIGGER_STATE cond;
		if (ch == source) {
			cond = PS3000A_CONDITION_TRUE;
		} else {
			cond = PS3000A_CONDITION_DONT_CARE;
		}
		setIntegerParam(P_ch_condition[ch], cond);
	}
	return setup_trigger();
}

int PS3000A::set_trigger_source() {
	int ch;
	epicsInt32 source;
	getIntegerParam(P_trigger_source, &source);

	for (ch = 0; ch < 4; ++ch) {
		PS3000A_TRIGGER_STATE cond;
		if (ch == source) {
			cond = PS3000A_CONDITION_TRUE;
		} else {
			cond = PS3000A_CONDITION_DONT_CARE;
		}
		setIntegerParam(P_ch_condition[ch], cond);
	}
	return setup_trigger();
}

int PS3000A::set_trigger_conditions() {
	PICO_STATUS ok;

	PS3000A_TRIGGER_CONDITIONS conditions[1];
	int16_t nConditions = 1;
	int ch;
	epicsInt32 connected;


	epicsInt32 ch_cond[4];
	for (ch = 0; ch < 4; ++ch) {
		getIntegerParam(P_ch_condition[ch], &ch_cond[ch]);
	}
	getIntegerParam(P_PicoConnected, &connected);

	/*printf("conditions: %d %d %d %d\n", ch_cond[0], ch_cond[1], ch_cond[2],
	    ch_cond[3]);*/

	conditions[0].channelA = (PS3000A_TRIGGER_STATE)ch_cond[0];
	conditions[0].channelB = (PS3000A_TRIGGER_STATE)ch_cond[1];
	conditions[0].channelC = (PS3000A_TRIGGER_STATE)ch_cond[2];
	conditions[0].channelD = (PS3000A_TRIGGER_STATE)ch_cond[3];
	conditions[0].external = PS3000A_CONDITION_DONT_CARE;
	conditions[0].aux = PS3000A_CONDITION_DONT_CARE;
	conditions[0].pulseWidthQualifier = PS3000A_CONDITION_DONT_CARE;

	if (connected != 0) {
		ok = ps3000aSetTriggerChannelConditions(ps.handle, conditions,
		    nConditions);
		CHKOK("SetTriggerChannelConditions");
	}

	return 0;
}

int PS3000A::set_trigger_directions() {
	PICO_STATUS ok;
	int ch;
	PS3000A_THRESHOLD_DIRECTION dir[4];
	epicsInt32 connected;

	getIntegerParam(P_PicoConnected, &connected);
	if (connected == 0) return PICO_INTERFACE_NOT_CONNECTED;

	for (ch = 0; ch < 4; ++ch) {
		epicsInt32 direction;
		getIntegerParam(P_ch_direction[ch], &direction);
		dir[ch] = (PS3000A_THRESHOLD_DIRECTION)direction;
	}

	PS3000A_THRESHOLD_DIRECTION ext = PS3000A_FALLING;
	PS3000A_THRESHOLD_DIRECTION aux = PS3000A_FALLING;

	ok = ps3000aSetTriggerChannelDirections(ps.handle, dir[0], dir[1],
	    dir[2], dir[3], ext, aux);
	CHKOK("SetTriggerChannelDirections");

	return 0;
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

int PS3000A::set_signal_generator() {
	PICO_STATUS ok;

	epicsInt32 offset_voltage;
	double pk_to_pk;
	epicsInt32 wave_type;
	epicsFloat64 start_frequency;
	epicsInt32 connected;
	epicsInt32 trigger_source;

	getIntegerParam(P_PicoConnected, &connected);
	getIntegerParam(P_sig_offset, &offset_voltage);
	getDoubleParam (P_sig_pktopk, &pk_to_pk);
	getIntegerParam(P_sig_wavetype, &wave_type);
	getDoubleParam (P_sig_frequency, &start_frequency);
	getIntegerParam(P_sig_trigger_source, &trigger_source);

	printf("signal generator: %d %f %d %f\n", offset_voltage, pk_to_pk,
	    wave_type, start_frequency);

	double stop_frequency = start_frequency;
	double increment = 1;
	double dwell_time = 1;
	PS3000A_SWEEP_TYPE sweep_type = PS3000A_UP;
	PS3000A_EXTRA_OPERATIONS operation = PS3000A_ES_OFF;
	uint32_t shots = 0;
	uint32_t sweeps = 0;
	PS3000A_SIGGEN_TRIG_TYPE trigger_type = PS3000A_SIGGEN_FALLING;
	trigger_source = PS3000A_SIGGEN_NONE;
	int16_t ext_in_threshold = 0;

	if (connected != 0) {
		/* Function takes values in micro-volts */
		int32_t offset_uV = offset_voltage * 1000000;
		int32_t pk_to_pk_uV = pk_to_pk * 1000000;
		ok = ps3000aSetSigGenBuiltInV2(ps.handle, offset_uV,
		    pk_to_pk_uV, wave_type, start_frequency, stop_frequency,
		    increment, dwell_time, sweep_type, operation, shots, sweeps,
		    trigger_type, (PS3000A_SIGGEN_TRIG_SOURCE)trigger_source,
		    ext_in_threshold);
		CHKOK("SetSigGenBuiltIn");
	}

	return 0;
}

int PS3000A::SetTimeBase() {
	PICO_STATUS ok;
	int ch;
	int channels_enabled;
	epicsInt32 max_points;
	epicsInt32 downsampled_frequency;
	epicsInt32 sample_frequency;
	epicsInt32 time_base;
	epicsInt32 max_samples = 0;
	epicsInt32 segment_index;
	epicsInt32 down_sample_ratio;
	epicsInt32 enabled[4] = {0};
	epicsInt32 samples_needed = 0;
	epicsInt32 samples_to_read = 0;
	float time_interval_ns = 0;
	double full_time_ns;
	double time_per_div_ns;
	epicsInt32 connected;

	getIntegerParam(P_PicoConnected, &connected);

	if (connected == 0) return PICO_INTERFACE_NOT_CONNECTED;

	/* We want to read at maximum about this amount of samples */
	getIntegerParam(P_MaxPoints, &max_points);

	/* Memory segment to use (usually 0) */
	getIntegerParam(P_segment_index, &segment_index);

	/* We want to read samples respresenting this time per division */
	getDoubleParam (P_TimePerDiv, &time_per_div_ns);
	getDoubleParam (P_FullTime, &full_time_ns);
	printf("Full time = %f ns\n", full_time_ns);

	/* Try to always use the lowest time base possible */
	channels_enabled = 0;
	for (ch = 0; ch < 4; ++ch) {
		getIntegerParam(P_ch_enabled[ch], &enabled[ch]);
		if (enabled[ch] != 0) channels_enabled++;
	}

	switch (channels_enabled) {
	case 0:
	case 1:
		time_base = 0;
		break;
	case 2:
		time_base = 1;
		break;
	case 3:
	case 4:
		time_base = 2;
		break;
	default:
		printf("Error: Illegal amount of channels enabled.\n");
		abort();
	}

	/* Find the lowest time base that can handle the requested time
	** per division and specified  number of samples.
	** Using ps3000aGetTimebase2() from API to get the time interval
	** in FLOAT rather than in INT32.
	*/
time_base_again:
	printf("Request time_base = %d\n", time_base);

	ok = ps3000aGetTimebase2(ps.handle, time_base, max_points,
	    &time_interval_ns, 0, &max_samples, segment_index);
	CHKOK("GetTimebase2");
	if (ok == PICO_INVALID_TIMEBASE) {
		time_base++;
		goto time_base_again;
	}

	printf("Final time_base = %d\n", time_base);
	ps.time_base = time_base;

	printf("Returned time_interval_ns = %f\n", time_interval_ns);
	setDoubleParam(P_time_interval_ns, time_interval_ns);
	ps.time_interval_ns = time_interval_ns;

	printf("Returned max_samples = %d\n", max_samples);
	setIntegerParam(P_max_samples, max_samples);

	sample_frequency = PS3000A_FREQUENCY / time_interval_ns;
	printf("Sample frequency = %d Hz\n", sample_frequency);
	setIntegerParam(P_sample_frequency, sample_frequency);

	/*
	 * How many samples do we need for the full_time?
	 */
	samples_needed = full_time_ns * (double)sample_frequency / 1.0e9;
	printf("Samples needed = %d\n", samples_needed);

	/*
	 * Do we need to downsample the data?
	 */
	if (samples_needed > max_points) {
		down_sample_ratio = ceil((double)samples_needed / (double)max_points);
	} else {
		down_sample_ratio = 1;
	}
	printf("Downsample ratio requested = %u\n", down_sample_ratio);
	setIntegerParam(P_down_sample_ratio, down_sample_ratio);

	downsampled_frequency = sample_frequency / down_sample_ratio;
	printf("Downsampled frequency = %d Hz\n", downsampled_frequency);
	setIntegerParam(P_downsampled_frequency, downsampled_frequency);

	/*
	 * How many samples do we need to read after downsampling?
	 */
	samples_to_read = ceil((double)samples_needed / (double)down_sample_ratio);
	printf("Samples to read = %d\n", samples_to_read);
	setIntegerParam(P_sample_length, samples_to_read);
	setIntegerParam(P_time_base_nelm, samples_to_read);

	return ok;
}

int PS3000A::set_data_buffer() {
	PICO_STATUS ok;
	int ch;

	epicsInt32 segment_index;
	epicsInt32 max_points;
	PS3000A_RATIO_MODE mode = PS3000A_RATIO_MODE_NONE;

	getIntegerParam(P_segment_index, &segment_index);
        getIntegerParam(P_MaxPoints, &max_points);

	for (ch = 0; ch < 4; ++ch) {
		ok = ps3000aSetDataBuffer(ps.handle, (PS3000A_CHANNEL) ch, data_buffer[ch], max_points, segment_index, mode);
	}

	CHKOK("SetDataBuffer");

	return 0;
}

PS3000A_RANGE get_best_range(int full_scale_mv) {
	int i;
	for (i = PS3000A_20MV; i < PS3000A_20V; ++i) {
		if (input_ranges[i] >= full_scale_mv) {
			break;
		}
	}
	return (PS3000A_RANGE)i;
}

void PS3000A::setVoltsPerDiv(int ch) {
    epicsInt32 mVPerDiv;
    int full_scale_mv;

    // Integer volts are in mV
    getIntegerParam(P_VoltsPerDivSelect[ch], &mVPerDiv);
    setDoubleParam(P_VoltsPerDiv[ch], mVPerDiv / 1000.);

    /* update channel range */
    full_scale_mv = mVPerDiv * NUM_DIVISIONS;
    PS3000A_RANGE range = get_best_range(full_scale_mv);

    /*printf("Full scale %d = %d mV\n", ch, full_scale_mv);
    printf("Optimal range %d = %d (enum)\n", ch, range);*/
    setIntegerParam(P_ch_range[ch], range);
    set_channel(ch);
}

int PS3000A::setup_trigger() {
	int ch;
	int ok;
	for (ch = 0; ch < 4; ch++) {
		ok = set_trigger(ch);
	}
	ok = set_trigger_directions();
	ok = set_trigger_conditions();
	return ok;
}

void PS3000A::ConnectPicoScope() {
	epicsInt32 connect, connected;
	getIntegerParam(P_PicoConnect, &connect);
	getIntegerParam(P_PicoConnected, &connected);

	printf("PICO connectPicoScope connect = %d\n", connect);

	if (connect == 0 && connected == 1) {
		// Device already connected, and an user issues a disconnect
		printf("PICO Disconnecting...\n");
		ClosePS3000A();
		setIntegerParam(P_PicoConnected, 0);
	} else if (connected == 0 && connect == 1) {
		// Device not connected, and an user issues a connect
		int ch;
		printf("PICO Connecting...\n");
		if(OpenPS3000A() != 0) {
			return;
		}
		for (ch = 0; ch < 4; ch++) {
			set_channel(ch);
		}

		PrintUnitInfo();

		SetTimeBase();
		setup_trigger();
		set_signal_generator();
		set_data_buffer();
	}
	// Any other case is a no-op
}

void PS3000A::setTimePerDiv() {
	epicsInt32 nsPerDiv;
	double time_per_div;
	double full_time_ns;

	// Integer times are in microseconds
	getIntegerParam(P_TimePerDivSelect, &nsPerDiv);
	time_per_div = (double)nsPerDiv;
	full_time_ns = time_per_div * NUM_DIVISIONS;
	setDoubleParam(P_TimePerDiv, time_per_div);
	setDoubleParam(P_FullTime, full_time_ns);

	printf("nsPerDiv = %d\n", nsPerDiv);
	printf("time_per_div = %f\n", time_per_div);

	set_time_base();
	setup_trigger();
};

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

