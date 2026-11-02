/*
 * Mpu9250: キットの 9 軸慣性センサ MPU-9250 を SPI で読み、加速度 [G] と角速度 [deg/s] を 10 Hz で表示する。
 *
 * 配線(センサのピン名は基板の裏面に書いてある):
 *   VCC → 3V3、GND → GND、SCLK → IO27、SDI → IO26(MOSI)、SDO → IO25(MISO)、NCS → IO33(CS)
 *
 * 地磁気(AK8963)はセンサの中の I2C の先にあるので、この例では読んでいない(AI に頼むときは
 * 「MPU-9250 の内部 I2C マスタ経由で AK8963 を読む」と伝える)。
 *
 * SPDX-License-Identifier: CC0-1.0
 */
#include <stdio.h>
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"
#include "esp_log.h"

#define PIN_SCLK 27
#define PIN_MOSI 26
#define PIN_MISO 25
#define PIN_CS   33

static spi_device_handle_t dev;

static void writeReg(uint8_t reg, uint8_t value){
    spi_transaction_t t = {.addr = reg & 0x7F, .length = 8, .flags = SPI_TRANS_USE_TXDATA, .tx_data = {value}};
    ESP_ERROR_CHECK(spi_device_polling_transmit(dev, &t));
}

static void readRegs(uint8_t reg, uint8_t *buf, int n){
    spi_transaction_t t = {.addr = reg | 0x80, .length = 8 * n, .rxlength = 8 * n, .rx_buffer = buf};
    ESP_ERROR_CHECK(spi_device_polling_transmit(dev, &t));
}

void app_main(void){
    spi_bus_config_t bus = {
        .mosi_io_num = PIN_MOSI, .miso_io_num = PIN_MISO, .sclk_io_num = PIN_SCLK,
        .quadwp_io_num = -1, .quadhd_io_num = -1, .max_transfer_sz = 32,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_DISABLED));
    spi_device_interface_config_t cfg = {
        .address_bits = 8,              //  最初の 1 バイトがレジスタ番号(読み出しは最上位ビットを 1 にする)
        .mode = 3,                      //  MPU-9250 は SPI モード 0 か 3
        .clock_speed_hz = 1000000,      //  レジスタの書き込みは 1 MHz まで
        .spics_io_num = PIN_CS,
        .queue_size = 1,
    };
    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &cfg, &dev));

    writeReg(0x6B, 0x80);               //  PWR_MGMT_1: リセット
    vTaskDelay(pdMS_TO_TICKS(100));
    writeReg(0x6B, 0x01);               //  PWR_MGMT_1: クロックを PLL に
    writeReg(0x6A, 0x10);               //  USER_CTRL: I2C を止めて SPI だけにする
    writeReg(0x1C, 0x00);               //  ACCEL_CONFIG: ±2 G
    writeReg(0x1B, 0x00);               //  GYRO_CONFIG: ±250 deg/s
    vTaskDelay(pdMS_TO_TICKS(10));

    uint8_t who = 0;
    readRegs(0x75, &who, 1);            //  WHO_AM_I: MPU-9250 は 0x71(互換品は 0x73、0x70 など)
    printf("WHO_AM_I = 0x%02X %s\r\n", who, who == 0x71 ? "(MPU-9250)" : "(check the wiring if 0x00 or 0xFF)");

    while (1){
        uint8_t b[14];
        readRegs(0x3B, b, 14);          //  ACCEL_XOUT_H から 14 バイト: 加速度 x,y,z、温度、角速度 x,y,z(上位バイトが先)
        int16_t v[7];
        for (int i = 0; i < 7; i++) v[i] = (int16_t)((b[2 * i] << 8) | b[2 * i + 1]);
        printf("accel: [%+6.2f %+6.2f %+6.2f] G   gyro: [%+8.2f %+8.2f %+8.2f] deg/s\r\n",
               v[0] / 16384.0, v[1] / 16384.0, v[2] / 16384.0, v[4] / 131.0, v[5] / 131.0, v[6] / 131.0);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
