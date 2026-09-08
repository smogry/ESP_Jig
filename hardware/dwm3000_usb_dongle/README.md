# DWM3000 USB Dongle (KiCad 7 project)

STM32F042F6P6 + Qorvo DWM3000 (UWB) USB dongle. Schematic capture is complete
and every part has a footprint assigned; PCB placement is an initial
non-overlapping layout only (routing is not done yet).

## Files

```
dwm3000_usb_dongle.kicad_pro    KiCad project
dwm3000_usb_dongle.kicad_sch    Schematic (single sheet)
dwm3000_usb_dongle.kicad_pcb    Board with all footprints placed + netlist wired (unrouted)
dwm3000_usb_dongle.net          Generated netlist (for reference / re-import)
dwm3000_usb_dongle_schematic.pdf  Schematic print, for quick review without KiCad
fp-lib-table                    Project footprint-library table (points at dongle.pretty)
dongle.pretty/                  Custom footprints (USB-A receptacle, SWD box header)
previews/                       Rendered PNG/SVG previews of the two custom footprints
scripts/gen_sch.py               Regenerates the .kicad_sch from scratch
scripts/build_pcb.py             Regenerates the .kicad_pcb from the .net file
```

To regenerate after editing a script: `python3 scripts/gen_sch.py` then re-export
the netlist (`kicad-cli sch export netlist ...`) and re-run `scripts/build_pcb.py`
(requires the `pcbnew` Python module, i.e. a full KiCad install).

## Bill of materials

| Ref | Part | Value | Footprint |
|---|---|---|---|
| U1 | STMicroelectronics STM32F042F6P6 | — | Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm |
| DWM1 | Qorvo DWM3000 module | — | RF_Module:DWM1000 (pin/pitch compatible per datasheet) |
| U2 | Torex XC6220B331MR-G | 3.3V LDO | Package_TO_SOT_SMD:SOT-23-5 (Torex "SOT-25" = JEDEC SOT-23-5) |
| J1 | USB-4AM103AS (Neltron 5075AR-04-XX-XX equivalent) | USB-A receptacle, right-angle THT | dongle:USB_A_Neltron_5075AR-04 (custom) |
| J2 | CnC Tech 3221-10-0300-00 | 1.27mm SMT box header, 2x5 | dongle:BoxHeader_2x05_P1.27mm_CnCTech_3221 (custom) |
| C1, C2 | Ceramic | 10uF | Capacitor_SMD:C_0805_2012Metric |
| C3, C4, C5, C7 | Ceramic | 100nF | Capacitor_SMD:C_0603_1608Metric |
| C6 | Ceramic | 1uF | Capacitor_SMD:C_0603_1608Metric |
| R1, R2 | USB D+/D- series | 22R | Resistor_SMD:R_0603_1608Metric |
| R3 | Status LED series | 1k | Resistor_SMD:R_0603_1608Metric |
| R4, R5 | TX/RX LED series | 330R | Resistor_SMD:R_0603_1608Metric |
| D1 | Status LED (MCU-driven) | LED | LED_SMD:LED_0603_1608Metric |
| D2 | TX activity LED (DWM3000 GPIO3/TXLED) | LED | LED_SMD:LED_0603_1608Metric |
| D3 | RX activity LED (DWM3000 GPIO2/RXLED) | LED | LED_SMD:LED_0603_1608Metric |

## Power tree

`USB VBUS (5V)` -> `U2 XC6220B331` -> `+3V3` -> STM32 VDD/VDDA, DWM3000
VDD1(AON)/VDD3V3 x2. U2's CE is tied directly to VIN (always enabled); it is
the "B" series part (CL auto-discharge, no CE pull-down needed).

## STM32F042F6P6 pin mapping (TSSOP-20)

| Pin | Name | Net | Notes |
|---|---|---|---|
| 1 | PB8 | LED1_CTRL | sinks D1 (status LED) |
| 2 | PF0 | NC | spare (no crystal needed, see below) |
| 3 | PF1 | NC | spare |
| 4 | NRST | NRST | to J2.10, 100nF to GND (C5) |
| 5 | VDDA | +3V3 | |
| 6 | PA0 | DWM_WAKEUP | drives DWM3000 WAKEUP |
| 7 | PA1 | DWM_RSTN | open-drain reset to DWM3000 RSTn |
| 8 | PA2 | DWM_IRQ | input, DWM3000 IRQ/GPIO8 |
| 9 | PA3 | SPI_CS | GPIO chip-select to DWM3000 SPICSn |
| 10 | PA4 | NC | spare |
| 11 | PA5 | SPI_SCK | SPI1_SCK |
| 12 | PA6 | SPI_MISO | SPI1_MISO |
| 13 | PA7 | SPI_MOSI | SPI1_MOSI |
| 14 | PB1 | NC | spare |
| 15 | VSSA | GND | |
| 16 | VDD | +3V3 | |
| 17 | PA9/PA11 | USB_DM_MCU | USB_DM alt-function pin (see remap note) |
| 18 | PA10/PA12 | USB_DP_MCU | USB_DP alt-function pin (see remap note) |
| 19 | PA13 | SWDIO | |
| 20 | PA14 | SWCLK | |

**No external crystal**: the STM32F042 has HSI48 with a USB-synchronized clock
recovery system (CRS), so USB full-speed works without an external crystal.
PF0/PF1 are therefore free GPIOs and left unconnected here.

**USB pin remap**: on the 20-pin package the physical pins are silkscreened
PA9/PA10, but firmware must set `SYSCFG_CFGR1.PA11_PA12_RMP=1` so they behave
electrically as PA11/PA12 (USB_DM/USB_DP) — this is the documented ST
mechanism for exposing USB on reduced-pin-count STM32F042 packages.

**No BOOT0 pin**: this package doesn't bring one out. Boot-from-bootloader is
selected via the `nBOOT0`/`nBOOT_SEL` option bytes through the SWD debugger
(e.g. STM32CubeProgrammer), not a physical strap.

## DWM3000 pin mapping (24-pin castellated module)

| Pin | Name | Net |
|---|---|---|
| 1 | EXTON | NC (device-enable output, unused) |
| 2 | WAKEUP | DWM_WAKEUP |
| 3 | RSTn | DWM_RSTN |
| 4 | GPIO7 | NC |
| 5 | VDD1 (AON) | +3V3 |
| 6, 7 | VDD3V3 | +3V3 |
| 8, 16, 21, 23, 24 | VSS | GND |
| 9–11, 14, 15 | GPIO6/5/4, GPIO1, GPIO0 | NC (spare) |
| 12 | GPIO3/TXLED | TXLED_CTRL -> D2 |
| 13 | GPIO2/RXLED | RXLED_CTRL -> D3 |
| 17 | SPICSn | SPI_CS |
| 18 | SPIMOSI | SPI_MOSI |
| 19 | SPIMISO | SPI_MISO |
| 20 | SPICLK | SPI_SCK |
| 22 | IRQ/GPIO8 | DWM_IRQ |

## SWD connector J2 (standard ARM 10-pin Cortex-Debug pinout)

| Pin | Signal | Net |
|---|---|---|
| 1 | VTref | +3V3 |
| 2 | SWDIO | SWDIO |
| 3, 5, 9 | GND | GND |
| 4 | SWCLK | SWCLK |
| 6 | SWO | NC (Cortex-M0 has no trace/SWO) |
| 7 | KEY | NC |
| 8 | TDI | NC (SWD only, no JTAG on Cortex-M0) |
| 10 | nRESET | NRST |

## Custom footprints

* **USB_A_Neltron_5075AR-04** — right-angle THT USB-A receptacle. Pad
  geometry (4x ⌀0.92 signal pins at 2.5/2.0mm pitch spanning 7.0mm, 2x ⌀2.3
  mounting pins spanning 13.14mm) matches the dimensions given in the
  connector's own datasheet (Neltron 5075AR-04-XX-XX).
* **BoxHeader_2x05_P1.27mm_CnCTech_3221** — 1.27mm-pitch SMT box header, 2x5,
  gull-wing pads, row spacing 2.76mm per the CnC Tech 3221-10-0300-00
  datasheet. Pin numbering follows the standard ARM SWD odd/even convention
  (pins 1,3,5,7,9 one row; 2,4,6,8,10 the other).

## Validation performed

* `kicad-cli sch export netlist` parses the schematic cleanly and produces
  the expected 16 signal nets + `+3V3`/`+5V`/`GND`, with every "spare"/unused
  pin explicitly flagged no-connect (verified pin-by-pin against the
  intended design above).
* All 20 components loaded their real KiCad footprints (including the 2
  custom ones) and were placed non-overlapping on a board with all 38 nets
  wired from the netlist (`dwm3000_usb_dongle.kicad_pcb`).
* Schematic and PCB were rendered to PDF/SVG/PNG for visual review.

## Not done yet (next steps for whoever picks this up)

* Final PCB placement (the current layout is just a tidy grid, grouped by
  subsystem) and routing.
* DRC / 3D check inside the KiCad GUI.
* Antenna keep-out area on the DWM3000 side per its datasheet §6.1 (no
  ground copper/components under or beside the module's ceramic antenna).
* USB D+/D- trace length matching + controlled impedance if desired.
