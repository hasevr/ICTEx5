/*
 * I2SHaptic: ActiveHaptic / SoftHaptics の波形を、モータードライバ(TB6612FNG)の代わりに
 * D 級アンプ MAX98357A(I2S 入力)で出力する版。
 *
 * - 波形は 16 kHz でサンプリングして I2S で送るので、ActiveHaptic(1 kHz)より高い周波数まできれいに出せる。
 * - 力センサの読み取り(IO34、ADC1 チャンネル6)と、しきい値で波形を始める考え方は ActiveHaptic / SoftHaptics と同じ。
 * - アクチュエータ(モータ・LRA・スピーカー)は MAX98357A の出力に 10 Ω と直列につなぐ。アンプの電源は 3.3 V。
 *
 * 配線: BCLK = IO26, LRC(WS) = IO25, DIN = IO22。TB6612FNG を挿したままにする場合、PWMA(IO16)を Low にして止める。
 *
 * SPDX-License-Identifier: CC0-1.0
 */

#include <stdio.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <esp_log.h>
#include <driver/uart.h>
#include <driver/gpio.h>
#include <driver/i2s_std.h>
#include <esp_adc/adc_oneshot.h>

static const char *TAG = "main";

//  I2S setting
#define SAMPLE_RATE     16000           //  Samples per second. MAX98357A accepts 8 kHz to 96 kHz.
#define BLOCK_FRAMES    32              //  Frames per block = 2 ms. The force sensor is read once per block (500 Hz).
#define DT              (1.0 / SAMPLE_RATE)  //  [s]
#define I2S_BCLK_IO     GPIO_NUM_26
#define I2S_WS_IO       GPIO_NUM_25
#define I2S_DOUT_IO     GPIO_NUM_22
#define TB6612_PWMA_IO  GPIO_NUM_16     //  Held low so that the motor driver (if still connected) stays off.

//  Safety: the output never exceeds this fraction of the full scale, whatever the parameters are.
#define AMP_LIMIT       0.6

//  ADC setting
static adc_oneshot_unit_handle_t adc1_handle;
static i2s_chan_handle_t tx_handle;

//  Thresholds of the force sensor (ADC value). Adjust them with "esp log" like ActiveHaptic / SoftHaptics.
static const int thresOn = 2400;        //  CLICK mode: start a wave when the ADC value exceeds this.
static const int thresOff = 2100;       //  CLICK mode: ready for the next wave when the ADC value falls below this.
static const int thresBase = 1900;      //  SOFT mode: ADC value when not touched.
#define NWAVE 10                        //  SOFT mode: number of thresholds (waves) while pushing in.
static const int thresStep = 15;        //  SOFT mode: ADC step between the thresholds.

//  Wave parameters, changed by the keys (see printHelp()).
static const double freqs[] = {20, 50, 100, 150, 200, 250, 300, 500, 1000, 2000};
#define NFREQ (sizeof(freqs) / sizeof(freqs[0]))
static const double damps[] = {-5, -10, -20, -50, -100, -200};
#define NDAMP (sizeof(damps) / sizeof(damps[0]))
static volatile int iFreq = 4;          //  200 Hz
static volatile int iDamp = 3;          //  -50
static volatile float amplitude = 0.3f; //  Fraction of the full scale (0 to AMP_LIMIT).
static volatile int softMode = 0;       //  0: CLICK (ActiveHaptic), 1: SOFT (SoftHaptics)
static volatile int squareWave = 0;     //  0: decaying cosine, 1: decaying square wave

static void printSettings(void){
    printf("Mode: %s, Wave: %s, %.0f Hz, B=%.0f, A=%.2f\r\n", softMode ? "SOFT" : "CLICK",
           squareWave ? "square" : "cos", freqs[iFreq], damps[iDamp], amplitude);
}

static void printHelp(void){
    printf("keys: f/F freq up/down, b/B damping stronger/weaker, a/A amplitude up/down, "
           "m CLICK/SOFT, w cos/square, p print\r\n");
}

//  A decaying wave, computed sample by sample with float only: the phase is rotated and the envelope is
//  multiplied by a constant every sample, so no cos()/exp() per sample (ESP32 has a float FPU but no double FPU).
struct Wave{
    float t;            //  Time from the start [s]. -1: not running.
    float re, im;       //  cos and sin of the phase.
    float env;          //  exp(B t)
};

static void startWave(struct Wave *w){
    w->t = 0; w->re = 1; w->im = 0; w->env = 1;
}

static void hapticTask(void *arg){
    int16_t buf[BLOCK_FRAMES * 2];      //  Stereo: the same sample on L and R. MAX98357A outputs (L+R)/2 by default.
    struct Wave waves[NWAVE];
    for (int w = 0; w < NWAVE; ++w) waves[w].t = -1;
    int count = 0;
    while (1){
        int ad = 0;
        adc_oneshot_read(adc1_handle, ADC_CHANNEL_6, &ad);
        //  Per-sample rotation and decay for the current parameters.
        float omega = (float)(freqs[iFreq] * M_PI * 2);
        float B = (float)damps[iDamp];
        float cw = cosf(omega * (float)DT), sw = sinf(omega * (float)DT);
        float kd = expf(B * (float)DT);
        //  Start / stop the waves according to the force.
        if (!softMode){
            if (ad < thresOff && waves[0].t > 0.3f) waves[0].t = -1;
            if (ad > thresOn && waves[0].t < 0){
                startWave(&waves[0]);
                printf("Click: %.0f Hz, B=%.0f, A=%.2f\r\n", freqs[iFreq], B, amplitude);
            }
        }else{
            for (int w = 0; w < NWAVE; ++w){
                int th = thresBase + (w + 1) * thresStep;
                if (waves[w].t >= 0 && ad < th - thresStep / 2) waves[w].t = -1;   //  Released below this threshold.
                else if (waves[w].t < 0 && ad > th) startWave(&waves[w]);
            }
        }
        //  Make one block of samples.
        float a = amplitude;
        if (a > AMP_LIMIT) a = AMP_LIMIT;
        int nw = softMode ? NWAVE : 1;
        for (int i = 0; i < BLOCK_FRAMES; ++i){
            float v = 0;
            for (int w = 0; w < nw; ++w){
                struct Wave *wv = &waves[w];
                if (wv->t < 0) continue;
                float c = squareWave ? (wv->re >= 0 ? 1.0f : -1.0f) : wv->re;
                v += c * wv->env;
                float re = wv->re * cw - wv->im * sw;
                wv->im = wv->re * sw + wv->im * cw;
                wv->re = re;
                wv->env *= kd;
                wv->t += (float)DT;
            }
            v *= a;
            if (v > AMP_LIMIT) v = AMP_LIMIT;
            if (v < -AMP_LIMIT) v = -AMP_LIMIT;
            int16_t s = (int16_t)(v * 32767);
            buf[2 * i] = s;
            buf[2 * i + 1] = s;
        }
        //  Keep |(re, im)| = 1 against rounding errors.
        for (int w = 0; w < nw; ++w){
            float m = sqrtf(waves[w].re * waves[w].re + waves[w].im * waves[w].im);
            if (m > 0){ waves[w].re /= m; waves[w].im /= m; }
        }
        size_t written = 0;
        i2s_channel_write(tx_handle, buf, sizeof(buf), &written, portMAX_DELAY);  //  Blocks until DMA has room: paces this loop.
        if (++count >= SAMPLE_RATE / BLOCK_FRAMES){     //  Once a second.
            ESP_LOGI("H_FUNC", "ADC:%d", ad);
            count = 0;
        }
    }
}

void app_main(void)
{
    printf("!!! I2S Haptic Start !!!\n");

    ESP_LOGI(TAG, "Initialize ADC");
    adc_oneshot_unit_init_cfg_t adc_init_config1 = {
        .unit_id = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&adc_init_config1, &adc1_handle));
    adc_oneshot_chan_cfg_t adc1_chan6_cfg = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &adc1_chan6_cfg));

    //  Keep the motor driver off in case it is still on the breadboard.
    gpio_config_t gpio_conf = {
        .pin_bit_mask = 1ULL << TB6612_PWMA_IO,
        .mode = GPIO_MODE_OUTPUT,
    };
    gpio_config(&gpio_conf);
    gpio_set_level(TB6612_PWMA_IO, 0);

    ESP_LOGI(TAG, "Initialize I2S");
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan_cfg.dma_desc_num = 3;                  //  Short DMA queue: about 6 ms from the sensor to the sound.
    chan_cfg.dma_frame_num = BLOCK_FRAMES;
    chan_cfg.auto_clear = true;                 //  Output silence if the task stops feeding data.
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, &tx_handle, NULL));
    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,            //  MAX98357A needs no MCLK.
            .bclk = I2S_BCLK_IO,
            .ws = I2S_WS_IO,
            .dout = I2S_DOUT_IO,
            .din = I2S_GPIO_UNUSED,
            .invert_flags = {0},
        },
    };
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(tx_handle, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(tx_handle));

    xTaskCreate(hapticTask, "Haptic", 1024 * 8, NULL, 6, NULL);

    printSettings();
    printHelp();
    uart_driver_install(UART_NUM_0, 1024, 1024, 10, NULL, 0);
    while(1){
        uint8_t ch;
        if (uart_read_bytes(UART_NUM_0, &ch, 1, portMAX_DELAY) <= 0 || ch == '\r' || ch == '\n') continue;
        switch(ch){
            case 'f': if (iFreq < NFREQ - 1) iFreq++; break;
            case 'F': if (iFreq > 0) iFreq--; break;
            case 'b': if (iDamp < NDAMP - 1) iDamp++; break;
            case 'B': if (iDamp > 0) iDamp--; break;
            case 'a': amplitude = fminf(amplitude + 0.05f, AMP_LIMIT); break;
            case 'A': amplitude = fmaxf(amplitude - 0.05f, 0.0f); break;
            case 'm': softMode = !softMode; break;
            case 'w': squareWave = !squareWave; break;
            case 'p': printHelp(); break;
            default: printf("'%c'?\r\n", ch); printHelp(); continue;
        }
        printSettings();
    }
}
