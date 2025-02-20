/* 
** Device support for PicoScope 3000 Series is written based on 
** the example of "testAsynPortDriver" from asyn module,
** the C/C++ example of "ps3000a" from Pico Technology
** (https://github.com/picotech/picosdk-c-examples/tree/master/ps3000a),
** and the "pico_2000" EPICS driver from GSI 
** (https://git.gsi.de/r3b_public/epics/pico_2000)
**
*/

#pragma once

#include "asynPortDriver.h"

#define NUM_VERT_SELECTIONS 12


/* These are the drvInfo strings that are used to identify the parameters.
 * They are used by asyn clients, including standard asyn device support */
#define P_RunString                "SCOPE_RUN"                    /* asynInt32,    r/w */
#define P_MaxPointsString          "SCOPE_MAX_POINTS"             /* asynInt32,    r/o */
#define P_TimePerDivString         "SCOPE_TIME_PER_DIV"           /* asynFloat64,  r/w */
#define P_FullTimeString           "SCOPE_FULL_TIME"              /* asynFloat64,  r/w */
#define P_TimePerDivSelectString   "SCOPE_TIME_PER_DIV_SELECT"    /* asynInt32,    r/w */
#define P_VoltsPerDivStringA       "SCOPE_VOLTS_PER_DIV_A"        /* asynFloat64,  r/w */
#define P_VoltsPerDivStringB       "SCOPE_VOLTS_PER_DIV_B"        /* asynFloat64,  r/w */
#define P_VoltsPerDivStringC       "SCOPE_VOLTS_PER_DIV_C"        /* asynFloat64,  r/w */
#define P_VoltsPerDivStringD       "SCOPE_VOLTS_PER_DIV_D"        /* asynFloat64,  r/w */
#define P_VoltsPerDivSelectStringA "SCOPE_VOLTS_PER_DIV_SELECT_A" /* asynInt32,    r/w */
#define P_VoltsPerDivSelectStringB "SCOPE_VOLTS_PER_DIV_SELECT_B" /* asynInt32,    r/w */
#define P_VoltsPerDivSelectStringC "SCOPE_VOLTS_PER_DIV_SELECT_C" /* asynInt32,    r/w */
#define P_VoltsPerDivSelectStringD "SCOPE_VOLTS_PER_DIV_SELECT_D" /* asynInt32,    r/w */
#define P_VoltOffsetStringA        "SCOPE_VOLT_OFFSET_A"          /* asynFloat64,  r/w */
#define P_VoltOffsetStringB        "SCOPE_VOLT_OFFSET_B"          /* asynFloat64,  r/w */
#define P_VoltOffsetStringC        "SCOPE_VOLT_OFFSET_C"          /* asynFloat64,  r/w */
#define P_VoltOffsetStringD        "SCOPE_VOLT_OFFSET_D"          /* asynFloat64,  r/w */
#define P_UpdateTimeString         "SCOPE_UPDATE_TIME"            /* asynFloat64,  r/w */
#define P_Waveform_StringA         "SCOPE_WAVEFORM_A"             /* asynFloat64Array,  r/o */
#define P_Waveform_StringB         "SCOPE_WAVEFORM_B"             /* asynFloat64Array,  r/o */
#define P_Waveform_StringC         "SCOPE_WAVEFORM_C"             /* asynFloat64Array,  r/o */
#define P_Waveform_StringD         "SCOPE_WAVEFORM_D"             /* asynFloat64Array,  r/o */
#define P_TriggerDelayString       "SCOPE_TRIGGER_DELAY"          /* asynFloat64,  r/w */
#define P_NoiseAmplitudeString     "SCOPE_NOISE_AMPLITUDE"        /* asynFloat64,  r/w */
#define P_TimeBaseString           "SCOPE_TIME_BASE"              /* asynFloat64Array,  r/o */
#define P_time_base_hopr_string    "time_base_hopr"
#define P_time_base_lopr_string    "time_base_lopr"
#define P_time_base_nelm_string    "time_base_nelm"
#define P_MinValueString           "SCOPE_MIN_VALUE"              /* asynFloat64,  r/o */
#define P_MaxValueString           "SCOPE_MAX_VALUE"              /* asynFloat64,  r/o */
#define P_MeanValueString          "SCOPE_MEAN_VALUE"             /* asynFloat64,  r/o */

#define P_PicoStatusString    "PICO_STATUS"
#define P_PicoConnectString   "PICO_CONNECT"
#define P_PicoConnectedString "PICO_CONNECTED"

#define P_max_samples_string           "max_samples"
#define P_time_interval_ns_string      "time_interval_ns"
#define P_sample_length_string         "sample_length"
#define P_sample_frequency_string      "sample_frequency"
#define P_downsampled_frequency_string "downsampled_frequency"
#define P_segment_index_string         "segment_index"
#define P_down_sample_ratio_string     "down_sample_ratio"
#define P_ch_A_overflow_string         "ch_A_overflow"
#define P_ch_A_enabled_string          "ch_A_enabled"
#define P_ch_A_offset_string           "ch_A_offset"
#define P_ch_A_range_string            "ch_A_range"
#define P_ch_A_coupling_string         "ch_A_coupling"
#define P_ch_A_threshold_string        "ch_A_threshold"
#define P_ch_A_condition_string        "ch_A_condition"
#define P_ch_A_direction_string        "ch_A_direction"
#define P_ch_B_overflow_string         "ch_B_overflow"
#define P_ch_B_enabled_string          "ch_B_enabled"
#define P_ch_B_offset_string           "ch_B_offset"
#define P_ch_B_range_string            "ch_B_range"
#define P_ch_B_coupling_string         "ch_B_coupling"
#define P_ch_B_threshold_string        "ch_B_threshold"
#define P_ch_B_condition_string        "ch_B_condition"
#define P_ch_B_direction_string        "ch_B_direction"
#define P_ch_C_overflow_string         "ch_C_overflow"
#define P_ch_C_enabled_string          "ch_C_enabled"
#define P_ch_C_offset_string           "ch_C_offset"
#define P_ch_C_range_string            "ch_C_range"
#define P_ch_C_coupling_string         "ch_C_coupling"
#define P_ch_C_threshold_string        "ch_C_threshold"
#define P_ch_C_condition_string        "ch_C_condition"
#define P_ch_C_direction_string        "ch_C_direction"
#define P_ch_D_overflow_string         "ch_D_overflow"
#define P_ch_D_enabled_string          "ch_D_enabled"
#define P_ch_D_offset_string           "ch_D_offset"
#define P_ch_D_range_string            "ch_D_range"
#define P_ch_D_coupling_string         "ch_D_coupling"
#define P_ch_D_threshold_string        "ch_D_threshold"
#define P_ch_D_condition_string        "ch_D_condition"
#define P_ch_D_direction_string        "ch_D_direction"

#define P_sig_offset_string         "sig_offset"
#define P_sig_pktopk_string         "sig_pktopk"
#define P_sig_wavetype_string       "sig_wavetype"
#define P_sig_frequency_string      "sig_frequency"
#define P_sig_trigger_source_string	"sig_trigger_source"

#define P_trigger_source_string     "trigger_source"

#include <ps3000aApi.h>

struct PS3000AChannel {
	PS3000A_RANGE    range;
	int              range_v;
	PS3000A_COUPLING coupling;
};

struct PS3000AConfig {
	PS3000AChannel ch[4];
};

struct BlockInfo {
	int16_t ready;
};

struct PS3000AModule {
	int16_t  handle;
	struct   PS3000AConfig config;
	int16_t  max_value;
	float    maximumVoltage;
	float    minimumVoltage;
	float    time_interval_ns;
	uint32_t time_base;
	int32_t  max_points;
	uint32_t max_down_sample_ratio;
};


class PS3000A : public asynPortDriver {
public:
    PS3000A(const char *portName, int maxArraySize);
                 
    /* These are the methods that we override from asynPortDriver */
    virtual asynStatus writeInt32(asynUser *pasynUser, epicsInt32 value);
    virtual asynStatus writeFloat64(asynUser *pasynUser, epicsFloat64 value);
    virtual asynStatus readFloat64Array(asynUser *pasynUser, epicsFloat64 *value, size_t nElements, size_t *nIn);
    virtual asynStatus readEnum(asynUser *pasynUser, char *strings[], int values[], int severities[], size_t nElements, size_t *nIn);

    /* These are the methods that are new to this class */
    void run_task(void);

protected:
    /** Values used for pasynUser->reason, and indexes into the parameter library. */
    int P_Run = 0;
    int P_MaxPoints = 0;
    int P_FullTime = 0;
    int P_TimePerDiv = 0;
    int P_TimePerDivSelect = 0;
    int P_VoltsPerDiv[4] = {0};
    int P_VoltsPerDivSelect[4] = {0};
    int P_VoltOffset[4] = {0};
    int P_Waveform[4] = {0};
    int P_TriggerDelay = 0;
    int P_NoiseAmplitude = 0;
    int P_UpdateTime = 0;
    int P_TimeBase = 0;
    int P_time_base_hopr = 0;
    int P_time_base_lopr = 0;
    int P_time_base_nelm = 0;
    int P_MinValue = 0;
    int P_MaxValue = 0;
    int P_MeanValue = 0;

    int P_PicoStatus = 0;
    int P_PicoConnect = 0;
    int P_PicoConnected = 0;

    /* Pico 3000a scope parameters */
    int P_max_samples = 0;
    int P_segment_index = 0;
    int P_downsampled_frequency = 0;
    int P_sample_frequency = 0;
    int P_sample_length = 0;
    int P_time_interval_ns = 0;
    int P_down_sample_ratio = 0;

    int P_ch_overflow[4] = {0};
    int P_ch_coupling[4] = {0};
    int P_ch_enabled[4] = {0};
    int P_ch_offset[4] = {0};
    int P_ch_range[4] = {0};
    int P_ch_threshold[4] = {0};
    int P_ch_condition[4] = {0};
    int P_ch_direction[4] = {0};

    /* Standard signal generator */
    int P_sig_offset = 0;
    int P_sig_pktopk = 0;
    int P_sig_wavetype = 0;
    int P_sig_frequency = 0;
    int P_sig_trigger_source = 0; 
   
    int P_trigger_source = 0; 
 
private:
    /* Our data */
    epicsEventId eventId_;
    epicsFloat64 *pData_[4];
    epicsFloat64 *pTimeBase_;
    // Actual volts per division are these values divided by vertical gain
    char *voltsPerDivStrings_[NUM_VERT_SELECTIONS];
    int voltsPerDivValues_[NUM_VERT_SELECTIONS];
    int voltsPerDivSeverities_[NUM_VERT_SELECTIONS];
    void setVoltsPerDiv(int);
    void setTimePerDiv();

    void ConnectPicoScope(void);
    int ClosePS3000A(void);
    int SetTimeBase(void);
    void set_time_base_array(void);
    int set_channel(int);
    int setup_trigger(void);
    int set_trigger(int);
    int set_trigger_directions(void);
    int set_trigger_conditions(void);
    int set_signal_generator(void);
    int set_data_buffer(void);
    int set_trigger_source();
    int set_sig_trigger_source();
    int pico_run_block(void);
    int OpenPS3000A(void);
    void PrintUnitInfo(void);

    int16_t mv_to_adc(int16_t, int);
    int32_t adc_to_uv(int32_t, int);
    float s_to_ns(int32_t);

    /* pico data members */
    int16_t *data_buffer[4];
    epicsInt32 max_sample_length;
    struct PS3000AModule ps;
};

#define CHKOK_OR_RETURN(name) do {\
	setIntegerParam(P_PicoStatus, ok);\
	if (ok != PICO_OK) {\
		printf("ERROR %d in %s: %s\n", ok, name, ps3000a_strings[ok]);\
		return ok;\
	}\
}while (0)
#define CHKOK(name) do {\
	setIntegerParam(P_PicoStatus, ok);\
	if (ok != PICO_OK) {\
		printf("ERROR %d in %s: %s\n", ok, name, ps3000a_strings[ok]);\
	}\
}while (0)

