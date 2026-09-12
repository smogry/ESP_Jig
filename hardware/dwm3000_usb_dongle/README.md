# DWM3000 USB Dongle (KiCad 7 project)

STM32C071F8P6 + Qorvo DWM3000 (UWB) USB dongle. Schematic capture is complete
and every part has a footprint assigned; PCB placement is an initial
non-overlapping layout only (routing is not done yet).

> **Rev history**: originally designed around an STM32F042F6P6; swapped to
> STM32C071F8P6 (same TSSOP20 footprint, but a different pinout — see the MCU
> section below for what changed: no NRST pin, no separate VDDA pin, and
> USB_DM/DP are native PA11/PA12 with no remap needed).

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
extra_symbols/STM32C071F8Px.kicad_sym  Upstream KiCad symbol for the MCU (source of
                                 truth for its pin table; not directly loadable by this
                                 project's KiCad 7.0.11 -- see note in gen_sch.py)
scripts/gen_sch.py               Regenerates the .kicad_sch from scratch
scripts/build_pcb.py             Regenerates the .kicad_pcb from the .net file
```

To regenerate after editing a script: `python3 scripts/gen_sch.py` then re-export
the netlist (`kicad-cli sch export netlist ...`) and re-run `scripts/build_pcb.py`
(requires the `pcbnew` Python module, i.e. a full KiCad install).

## Bill of materials

| Ref | Part | Value | Footprint |
|---|---|---|---|
| U1 | STMicroelectronics STM32C071F8P6 | — | Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm |
| DWM1 | Qorvo DWM3000 module | — | RF_Module:DWM1000 (pin/pitch compatible per datasheet) |
| U2 | Torex XC6220B331MR-G | 3.3V LDO | Package_TO_SOT_SMD:SOT-23-5 (Torex "SOT-25" = JEDEC SOT-23-5) |
| J1 | USB-4AM103AS (Neltron 5075AR-04-XX-XX equivalent) | USB-A receptacle, right-angle THT | dongle:USB_A_Neltron_5075AR-04 (custom) |
| J2 | CnC Tech 3221-10-0300-00 | 1.27mm SMT box header, 2x5 | dongle:BoxHeader_2x05_P1.27mm_CnCTech_3221 (custom) |
| C1, C2 | Ceramic | 10uF | Capacitor_SMD:C_0805_2012Metric |
| C3, C7 | Ceramic | 100nF | Capacitor_SMD:C_0603_1608Metric |
| C6 | Ceramic | 1uF | Capacitor_SMD:C_0603_1608Metric |
| R1, R2 | USB D+/D- series | 22R | Resistor_SMD:R_0603_1608Metric |
| R6 | **DNP** — optional USB D+ pull-up (fitted only if needed, see below) | 1.5k | Resistor_SMD:R_0603_1608Metric |
| R3 | Status LED series | 1k | Resistor_SMD:R_0603_1608Metric |
| R4, R5 | TX/RX LED series | 330R | Resistor_SMD:R_0603_1608Metric |
| D1 | Status LED (MCU-driven) | LED | LED_SMD:LED_0603_1608Metric |
| D2 | TX activity LED (DWM3000 GPIO3/TXLED) | LED | LED_SMD:LED_0603_1608Metric |
| D3 | RX activity LED (DWM3000 GPIO2/RXLED) | LED | LED_SMD:LED_0603_1608Metric |

## Power tree

`USB VBUS (5V)` -> `U2 XC6220B331` -> `+3V3` -> STM32 VDD, DWM3000
VDD1(AON)/VDD3V3 x2. U2's CE is tied directly to VIN (always enabled); it is
the "B" series part (CL auto-discharge, no CE pull-down needed).

## STM32C071F8P6 pin mapping (TSSOP-20)

Pin table taken from the official KiCad symbol (`MCU_ST_STM32C0:STM32C071F8Px`,
ST-generated data, Oct 2024 — see `extra_symbols/STM32C071F8Px.kicad_sym`).

| Pin | Name | Net | Notes |
|---|---|---|---|
| 1 | PB7/PB8 | LED1_CTRL | sinks D1 (status LED) |
| 2 | PC14 | NC | spare |
| 3 | PC15 | NC | spare |
| 4 | VDD | +3V3 | single supply pin (no separate VDDA on this package) |
| 5 | VSS | GND | |
| 6 | PF2 | NC | spare |
| 7 | PA0 | DWM_WAKEUP | drives DWM3000 WAKEUP |
| 8 | PA1 | DWM_RSTN | open-drain reset to DWM3000 RSTn |
| 9 | PA2 | DWM_IRQ | input, DWM3000 IRQ/GPIO8 |
| 10 | PA3 | SPI_CS | GPIO chip-select to DWM3000 SPICSn |
| 11 | PA4 | NC | spare |
| 12 | PA5 | SPI_SCK | SPI1_SCK |
| 13 | PA6 | SPI_MISO | SPI1_MISO |
| 14 | PA7 | SPI_MOSI | SPI1_MOSI |
| 15 | PA8 | NC | spare |
| 16 | PA11 | USB_DM_MCU | native USB_DM (no remap needed, see below) |
| 17 | PA12 | USB_DP_MCU | native USB_DP (no remap needed, see below) |
| 18 | PA13 | SWDIO | |
| 19 | PA14/PA15 | SWCLK | |
| 20 | PB3/PB4/PB5/PB6 | NC | spare |

**No external crystal**: like the F042 this replaced, STM32C071 has HSI48
with a USB-synchronized clock recovery system (CRS), so USB full-speed works
without an external crystal.

**USB pins are native, no remap**: unlike the STM32F042F6P6 this replaced
(which only exposed PA9/PA10 and needed `SYSCFG_CFGR1.PA11_PA12_RMP=1` to use
them as USB), this package brings out true PA11 (USB_DM) and PA12 (USB_DP)
directly on pins 16/17 — firmware just needs to enable the USB peripheral,
no pin remap step required.

**Optional USB D+ pull-up (R6, DNP by default)**: every ST full-speed USB
device peripheral in this IP family (F0/G0/L0/C0) has always had a
software-controlled internal D+ pull-up (`USB_BCDR.DPPU`), so no external
one should be needed here either — but this project's tools couldn't reach
st.com to confirm that against the STM32C071 reference manual directly, so
**R6** (1.5k, USB_DP_MCU to +3V3, right at the R2/PA12 side) is included as
a footprint-only safety net: leave it unpopulated (its default `DNP` state)
and bring the board up first. Only stuff R6 if enumeration fails or the
device isn't detected as full-speed, which would indicate the internal
pull-up either isn't present or isn't enabled by your firmware.

**No NRST pin on this package**: unlike the F042F6P6, this specific
TSSOP20 STM32C0 variant has no dedicated reset pin at all (18 GPIO instead —
ST traded the reset pin for one more GPIO). Consequences:
* J2 pin 10 (nRESET) has nothing to connect to on the MCU side and is left
  no-connect. A hardware "connect under reset" isn't possible; use a normal
  SWD connect and the debugger's software `AIRCR.SYSRESETREQ` reset instead
  (works fine with ST-Link/OpenOCD/PyOCD for normal flashing and debugging).
* There is no discrete NRST filter capacitor in this design (the previous
  100nF C5 was removed along with the pin it filtered).

**No separate VDDA pin either**: this package has a single VDD/VSS supply
pair (no analog supply pin to decouple separately), so there's one 100nF
decoupling cap (C3) instead of the F042's two.

**No BOOT0 pin**: same situation as before — boot-from-bootloader is
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
| 6 | SWO | NC (Cortex-M0+ has no trace/SWO) |
| 7 | KEY | NC |
| 8 | TDI | NC (SWD only, no JTAG on Cortex-M0+) |
| 10 | nRESET | NC (STM32C071F8Px has no NRST pin, see MCU section above) |

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
  intended design above, including J2 pin 10 now that the MCU has no NRST).
* All 19 components (18 fitted + DNP R6) loaded their real KiCad footprints
  (including the 2 custom ones) and were placed non-overlapping on a board
  with all 40 nets wired from the netlist (`dwm3000_usb_dongle.kicad_pcb`).
  R6 is marked excluded from BOM/position files to match its schematic DNP flag.
* Schematic and PCB were rendered to PDF/SVG/PNG for visual review.

### A note on the STM32C071F8Px symbol

This project's KiCad install (7.0.11, the current Ubuntu package) ships a
`MCU_ST_STM32C0` library that only goes up to STM32C011/STM32C031 —
STM32C071 was added to the official KiCad libraries later, in a newer
generator format (KiCad 9/10-style, e.g. `show_name`/`do_not_autoplace`
sub-fields) that this KiCad 7.0.11 cannot parse. `extra_symbols/STM32C071F8Px.kicad_sym`
is the real upstream symbol (fetched from the current kicad-symbols `master`
on GitLab) kept here as the authoritative source for the pin table; `scripts/gen_sch.py`
reproduces the same pins in the older, KiCad-7-compatible symbol syntax
(`build_stm32c071_symbol()`) rather than embedding that file directly. If/when
this project is opened in a newer KiCad, the vendored symbol can be dropped in
as-is.

## Not done yet (next steps for whoever picks this up)

* Final PCB placement (the current layout is just a tidy grid, grouped by
  subsystem) and routing.
* DRC / 3D check inside the KiCad GUI.
* Antenna keep-out area on the DWM3000 side per its datasheet §6.1 (no
  ground copper/components under or beside the module's ceramic antenna).
* USB D+/D- trace length matching + controlled impedance if desired.
