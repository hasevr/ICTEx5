/*
 * HttpHaptic: ActiveHaptic(力センサで押すとモータが減衰振動する)に、無線LAN と HTTP の通信を加えたもの。
 *
 * - 一定間隔(既定 500 ms)ごとに、力センサの A/D 変換値と時刻を、Raspberry Pi の Web サーバに HTTP GET で送る。
 *     GET /getadc?ADC=1975&TIME=12.345
 * - サーバの応答(JSON)に "freq": 数値 があれば、その周波数で振動させる(0 なら、押すたびに周波数を切り替える)。
 * - 無線LAN とサーバの宛先は、シリアルのコマンドで変えられ、ESP32 の不揮発メモリ(NVS)に保存される。
 *     server 10.0.1.23:50000      サーバ(Raspberry Pi の IP アドレスとポート)
 *     interval 200                送る間隔 [ms]
 *     wifi SSID PASSWORD          無線LAN(保存して再起動)
 *     show                        設定の表示
 *   Colab からは  esp send "server 10.0.1.23:50000\n"  のように送る。
 *
 * ピン割り当ては ActiveHaptic と同じ(力センサ IO34 = ADC1 チャンネル6、TB6612FNG: IO5 = AIN1、IO17 = AIN2、IO16 = PWMA)。
 *
 * SPDX-License-Identifier: CC0-1.0
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_http_client.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "bdc_motor.h"

static const char *TAG = "main";

/* ------------------------------------------------------------------ 設定(NVS に保存) */
static char cfgSsid[33] = CONFIG_HH_WIFI_SSID;
static char cfgPass[65] = CONFIG_HH_WIFI_PASSWORD;
static char cfgServer[64] = CONFIG_HH_SERVER;
static volatile int cfgIntervalMs = CONFIG_HH_INTERVAL_MS;

static void loadConfig(void){
    nvs_handle_t h;
    if (nvs_open("hh", NVS_READONLY, &h) != ESP_OK) return;
    size_t n;
    n = sizeof(cfgSsid);   nvs_get_str(h, "ssid", cfgSsid, &n);
    n = sizeof(cfgPass);   nvs_get_str(h, "pass", cfgPass, &n);
    n = sizeof(cfgServer); nvs_get_str(h, "server", cfgServer, &n);
    int32_t v;
    if (nvs_get_i32(h, "interval", &v) == ESP_OK) cfgIntervalMs = v;
    nvs_close(h);
}

static void saveStr(const char *key, const char *value){
    nvs_handle_t h;
    if (nvs_open("hh", NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_str(h, key, value);
    nvs_commit(h);
    nvs_close(h);
}

static void saveInt(const char *key, int value){
    nvs_handle_t h;
    if (nvs_open("hh", NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_i32(h, key, value);
    nvs_commit(h);
    nvs_close(h);
}

static void showConfig(void){
    printf("Wi-Fi: %s, server: %s, interval: %d ms\r\n", cfgSsid, cfgServer[0] ? cfgServer : "(not set)", cfgIntervalMs);
}

/* ------------------------------------------------------------------ 触覚提示(ActiveHaptic と同じ) */
#define DT (1.0 / configTICK_RATE_HZ)   //  1 ms(FreeRTOS の周期 1 kHz)
static adc_oneshot_unit_handle_t adc1_handle;
static bdc_motor_handle_t motor = NULL;
#define BDC_MCPWM_TIMER_RESOLUTION_HZ 10000000
#define BDC_MCPWM_FREQ_HZ             25000
#define BDC_MCPWM_DUTY_TICK_MAX       (BDC_MCPWM_TIMER_RESOLUTION_HZ / BDC_MCPWM_FREQ_HZ)

static const double freqs[] = {10, 20, 50, 100, 200, 500};
#define NFREQ (sizeof(freqs) / sizeof(freqs[0]))
static const double damps[] = {-2, -5, -10};
#define NDAMP (sizeof(damps) / sizeof(damps[0]))
static const double amplitude = 2;

static volatile int adValue = 0;        //  最新の A/D 変換値
static volatile double timeReadAdc = 0; //  それを読んだ時刻 [s](起動からの時間)
static volatile double serverFreq = 0;  //  サーバから指定された周波数 [Hz]。0 なら押すたびに切り替える

static void hapticTask(void *arg){
    int i = 0;
    double omega = 0, B = 0, since = -1;
    while (1){
        int ad = 0;
        adc_oneshot_read(adc1_handle, ADC_CHANNEL_6, &ad);
        adValue = ad;
        timeReadAdc = esp_timer_get_time() * 1e-6;
        if (ad < 2100 && since > 0.3) since = -1;
        if (ad > 2400 && since == -1){
            since = 0;
            double f = serverFreq > 0 ? serverFreq : freqs[i % NFREQ];
            omega = f * M_PI * 2;
            B = damps[(i / NFREQ) % NDAMP];
            printf("Wave: %3.1f Hz, B=%3.1f\r\n", f, B);
            i++;
        }
        double pwm = 0;
        if (since >= 0){
            pwm = amplitude * cos(omega * since) * exp(B * since);
            since += DT;
        }
        if (pwm > 0) bdc_motor_forward(motor);
        else { bdc_motor_reverse(motor); pwm = -pwm; }
        if (pwm > 1) pwm = 1;       //  出力の上限(消さないこと)
        bdc_motor_set_speed(motor, (unsigned)(pwm * BDC_MCPWM_DUTY_TICK_MAX));
        vTaskDelay(1);
    }
}

/* ------------------------------------------------------------------ 無線LAN */
static EventGroupHandle_t wifiEvents;
#define WIFI_CONNECTED BIT0

static void wifiHandler(void *arg, esp_event_base_t base, int32_t id, void *data){
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START){
        esp_wifi_connect();
    }else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED){
        xEventGroupClearBits(wifiEvents, WIFI_CONNECTED);
        ESP_LOGW(TAG, "Wi-Fi disconnected, retrying");
        vTaskDelay(pdMS_TO_TICKS(1000));
        esp_wifi_connect();
    }else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP){
        ip_event_got_ip_t *e = (ip_event_got_ip_t *)data;
        ESP_LOGI(TAG, "Wi-Fi connected, my IP: " IPSTR, IP2STR(&e->ip_info.ip));
        xEventGroupSetBits(wifiEvents, WIFI_CONNECTED);
    }
}

static void wifiStart(void){
    wifiEvents = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifiHandler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifiHandler, NULL));
    wifi_config_t wc = {0};
    strncpy((char *)wc.sta.ssid, cfgSsid, sizeof(wc.sta.ssid));
    strncpy((char *)wc.sta.password, cfgPass, sizeof(wc.sta.password));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_LOGI(TAG, "Connecting to Wi-Fi '%s'", cfgSsid);
}

/* ------------------------------------------------------------------ HTTP でサーバに送る */
static void httpTask(void *arg){
    char url[160];
    char resp[256];
    while (1){
        vTaskDelay(pdMS_TO_TICKS(cfgIntervalMs));
        if (!(xEventGroupGetBits(wifiEvents) & WIFI_CONNECTED)) continue;
        if (!cfgServer[0]){
            static int warned = 0;
            if (!warned++) printf("Server is not set. Send e.g. 'server 10.0.1.23:50000'\r\n");
            continue;
        }
        snprintf(url, sizeof(url), "http://%s/getadc?ADC=%d&TIME=%.3f", cfgServer, adValue, timeReadAdc);
        esp_http_client_config_t hc = {
            .url = url,
            .timeout_ms = 3000,
        };
        esp_http_client_handle_t client = esp_http_client_init(&hc);
        int64_t t0 = esp_timer_get_time();
        esp_err_t err = esp_http_client_open(client, 0);
        int status = -1, len = 0;
        if (err == ESP_OK){
            esp_http_client_fetch_headers(client);
            status = esp_http_client_get_status_code(client);
            len = esp_http_client_read_response(client, resp, sizeof(resp) - 1);
            if (len < 0) len = 0;
        }
        resp[len] = 0;
        double rtt = (esp_timer_get_time() - t0) * 1e-3;
        esp_http_client_cleanup(client);
        if (err != ESP_OK){
            ESP_LOGW(TAG, "HTTP failed: %s (%s)", esp_err_to_name(err), url);
            continue;
        }
        //  応答の例: {"adc": 1975, "freq": 200}
        char *p = strstr(resp, "\"freq\"");
        if (p && (p = strchr(p, ':'))){
            double f = atof(p + 1);
            if (f != serverFreq){
                serverFreq = f;
                printf("Frequency from server: %.1f Hz\r\n", f);
            }
        }
        ESP_LOGI("HTTP", "status=%d rtt=%.1f ms ADC=%d resp=%s", status, rtt, adValue, resp);
    }
}

/* ------------------------------------------------------------------ シリアルのコマンド */
static void handleLine(char *line){
    char *cmd = strtok(line, " ");
    if (!cmd) return;
    char *a1 = strtok(NULL, " ");
    char *a2 = strtok(NULL, " ");
    if (!strcmp(cmd, "server") && a1){
        strncpy(cfgServer, a1, sizeof(cfgServer) - 1);
        saveStr("server", cfgServer);
        showConfig();
    }else if (!strcmp(cmd, "interval") && a1){
        int v = atoi(a1);
        if (v < 10) v = 10;
        cfgIntervalMs = v;
        saveInt("interval", v);
        showConfig();
    }else if (!strcmp(cmd, "wifi") && a1){
        saveStr("ssid", a1);
        saveStr("pass", a2 ? a2 : "");
        printf("Wi-Fi settings saved. Restarting...\r\n");
        vTaskDelay(pdMS_TO_TICKS(200));
        esp_restart();
    }else if (!strcmp(cmd, "show")){
        showConfig();
    }else{
        printf("commands: server HOST:PORT / interval MS / wifi SSID PASSWORD / show\r\n");
    }
}

void app_main(void){
    printf("!!! HttpHaptic Start !!!\r\n");
    esp_err_t r = nvs_flash_init();
    if (r == ESP_ERR_NVS_NO_FREE_PAGES || r == ESP_ERR_NVS_NEW_VERSION_FOUND){
        nvs_flash_erase();
        r = nvs_flash_init();
    }
    ESP_ERROR_CHECK(r);
    loadConfig();
    showConfig();

    //  A/D 変換(力センサ)
    adc_oneshot_unit_init_cfg_t adcCfg = {.unit_id = ADC_UNIT_1, .ulp_mode = ADC_ULP_MODE_DISABLE};
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&adcCfg, &adc1_handle));
    adc_oneshot_chan_cfg_t chCfg = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_12};
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &chCfg));

    //  モータードライバ(PWMA は常に High)
    gpio_config_t g = {.pin_bit_mask = 1ULL << GPIO_NUM_16, .mode = GPIO_MODE_OUTPUT};
    gpio_config(&g);
    gpio_set_level(GPIO_NUM_16, 1);
    bdc_motor_config_t mc = {.pwma_gpio_num = GPIO_NUM_5, .pwmb_gpio_num = GPIO_NUM_17, .pwm_freq_hz = BDC_MCPWM_FREQ_HZ};
    bdc_motor_mcpwm_config_t pc = {.group_id = 0, .resolution_hz = BDC_MCPWM_TIMER_RESOLUTION_HZ};
    ESP_ERROR_CHECK(bdc_motor_new_mcpwm_device(&mc, &pc, &motor));
    ESP_ERROR_CHECK(bdc_motor_enable(motor));

    //  触覚提示はコア1で(無線LAN の処理はコア0で動く)
    xTaskCreatePinnedToCore(hapticTask, "Haptic", 1024 * 8, NULL, 6, NULL, 1);

    wifiStart();
    xTaskCreate(httpTask, "http", 1024 * 6, NULL, 5, NULL);

    //  シリアルから1行ずつコマンドを受け取る
    uart_driver_install(UART_NUM_0, 1024, 1024, 10, NULL, 0);
    char line[128];
    int n = 0;
    while (1){
        uint8_t ch;
        if (uart_read_bytes(UART_NUM_0, &ch, 1, portMAX_DELAY) <= 0) continue;
        if (ch == '\r' || ch == '\n'){
            if (n){ line[n] = 0; handleLine(line); n = 0; }
        }else if (n < (int)sizeof(line) - 1){
            line[n++] = ch;
        }
    }
}
