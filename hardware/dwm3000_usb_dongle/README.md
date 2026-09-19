# DWM3000 USB Dongle (KiCad 7 project)

STM32C071F8P6 + Qorvo DWM3000 (UWB) USB dongle. Schematic capture is complete
and every part has a footprint assigned; PCB placement is an initial
non-overlapping layout only (routing is not done yet).

> **Rev history**: originally designed around an STM32F042F6P6; swapped to
> STM32C071F8P6 (same TSSOP20 footprint, but a different pinout — see the MCU
> section below for what changed: PF2/NRST is a shared pin instead of a
> dedicated NRST, no separate VDDA pin, and USB_DM/DP are native PA11/PA12
> with no remap needed). A previous revision of this README incorrectly said
> this package "has no NRST pin at all" and left it unconnected -- that was
> wrong (see the corrected MCU section below); pin 6 is wired to J2 nRESET now.

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
| C3, C5, C7 | Ceramic | 100nF | Capacitor_SMD:C_0603_1608Metric |
| C6 | Ceramic | 1uF | Capacitor_SMD:C_0603_1608Metric |
| R1, R2 | USB D+/D- series | 22R | Resistor_SMD:R_0603_1608Metric |
| R6 | **DNP** — optional USB D+ pull-up (fitted only if needed, see below) | 1.5k | Resistor_SMD:R_0603_1608Metric |
| R3 | Status LED series | 1k | Resistor_SMD:R_0603_1608Metric |
| R4, R5 | TX/RX LED series | 330R | Resistor_SMD:R_0603_1608Metric |
| R7 | Second status LED series | 1k | Resistor_SMD:R_0603_1608Metric |
| R9 | Power-indicator LED series | 1k | Resistor_SMD:R_0603_1608Metric |
| D1 | Status LED 1 (MCU-driven, PB7/PB8) | LED | LED_SMD:LED_0603_1608Metric |
| D2 | TX activity LED (DWM3000 GPIO3/TXLED) | LED | LED_SMD:LED_0603_1608Metric |
| D3 | RX activity LED (DWM3000 GPIO2/RXLED) | LED | LED_SMD:LED_0603_1608Metric |
| D4 | Status LED 2 (MCU-driven, PB3) | LED | LED_SMD:LED_0603_1608Metric |
| D5 | Power indicator LED (always on, not MCU-driven) | LED | LED_SMD:LED_0603_1608Metric |
| U3 | ST USBLC6-2SC6 | USB D+/D- ESD protection | Package_TO_SOT_SMD:SOT-23-6 |
| F1 | Resettable PTC fuse, VBUS input | 500mA | Fuse:Fuse_0603_1608Metric |
| C4 | Ceramic, VBUS HF bypass (ahead of F1) | 100nF | Capacitor_SMD:C_0603_1608Metric |
| C8 | Ceramic, VBUS HF bypass (LDO input, parallel with C1) | 100nF | Capacitor_SMD:C_0603_1608Metric |

## Power tree

`USB VBUS` -> `J1 pin1` -> `C4 (100nF HF bypass)` -> `F1 (500mA PTC fuse)` ->
`+5V` -> `C1 (10uF) / C8 (100nF)` -> `U2 XC6220B331` -> `+3V3` -> STM32 VDD,
DWM3000 VDD1(AON)/VDD3V3 x2, and D5/R9 (always-on power-indicator LED). U2's
CE is tied directly to VIN (always enabled); it is the "B" series part (CL
auto-discharge, no CE pull-down needed).

`J1 D-/D+` -> `U3 (USBLC6-2SC6 ESD protection)` -> `R1/R2 (22R series)` ->
STM32 PA11/PA12 (USB_DM/USB_DP).

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
| 6 | PF2-NRST | NRST | shared pin, defaults to reset input (see below); to J2.10, 100nF to GND (C5) |
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
| 20 | PB3/PB4/PB5/PB6 | LED2_CTRL | sinks D4 (2nd status LED), using the PB3 identity -- see below |

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

## USB protection, VBUS filtering, power indicator

* **U3 (USBLC6-2SC6)**: dual-line, low-capacitance ESD protection diode
  array (SOT-23-6), inserted in series on D-/D+ between the connector (J1)
  and the existing series resistors (R1/R2) feeding the MCU. Its VBUS pin
  is tied to the (post-fuse) `+5V` rail as the clamp reference, per its
  datasheet. This does not replace R1/R2 — both stay in place downstream
  of U3.
* **F1 (500mA resettable PTC fuse) + C4/C8 (100nF HF bypass)**: VBUS from
  the connector now passes through a small HF bypass cap (C4, right at the
  connector) and a resettable fuse (F1) before becoming the board's `+5V`
  rail; C8 adds a second HF bypass cap at the LDO input, alongside the
  existing bulk cap C1. This protects the host's USB port (and this board)
  from an accidental VBUS short or overcurrent fault downstream, and the
  extra HF caps improve high-frequency supply noise rejection beyond what
  the two 10uF bulk caps (C1/C2) alone provide.
* **D5/R9 (always-on power indicator LED)**: wired straight across `+3V3`
  and `GND` (not MCU-driven, unlike D1/D4), so it lights whenever the LDO
  output is good — independent of firmware/MCU state, useful for confirming
  the board is powered even if the MCU isn't running.

**Pin 6 is a shared PF2/NRST pin, not a dedicated NRST**: unlike the
F042F6P6's pin 4 (a dedicated NRST-only pin), pin 6 on this package is
named **PF2-NRST** in ST's own pin database. This was missed in an earlier
revision of this project: the KiCad symbol used to derive the pin table
(`extra_symbols/STM32C071F8Px.kicad_sym`) only lists this pin's normal
GPIO alternate functions (`PF2`, `RCC_MCO`, `TIM1_CH4`) because the
reset/GPIO duality isn't a regular alternate function — it's controlled by
the **`NRST_MODE[1:0]` option byte**, which isn't part of a KiCad symbol's
pin table at all. Cross-checked against ST's public
[STM32_open_pin_data](https://github.com/STMicroelectronics/STM32_open_pin_data)
MCU database, which does carry the pin's real name (`PF2-NRST`).

Consequences of that, now fixed:
* **Out of the box (factory-default option bytes) this pin behaves as a
  normal NRST reset input**, so it's wired to J2 pin 10 (nRESET) like any
  other STM32 design, with a 100nF filter cap (C5) per the usual
  ST hardware design guidelines (AN2586). Hardware "connect under reset"
  works normally with ST-Link/OpenOCD/PyOCD.
* Firmware *can* reclaim this pin as a plain GPIO (`PF2`) by setting
  `NRST_MODE[1:0]` = GPIO in the option bytes — but this project does not
  do that, and doing so is not recommended without a specific need: ST's
  own community forum documents real pitfalls (the pin still gates
  power-on reset until it sees a valid `VIH(NRST)` level even in GPIO mode,
  and it's possible to end up unable to re-enter reset/debug mode without a
  recovery procedure). Leave `NRST_MODE` at its default and use J2/NRST for
  hardware reset as wired here.

**No separate VDDA pin either**: this package has a single VDD/VSS supply
pair (no analog supply pin to decouple separately), so there's one 100nF
decoupling cap (C3) instead of the F042's two.

**PA14 (SWCLK) is also a shared BOOT0 pin, but it's dormant by default**:
ST's pin database names pin 19 **PA14-BOOT0** — after the PF2-NRST finding
above, this project audited the STM32_open_pin_data XML for every other pin
with a similar hyphenated (option-byte-special) name and found exactly two
more: `PA14-BOOT0` and the OSC pins below. Unlike NRST, this one needed no
hardware fix: **`nBOOT_SEL` defaults to 1 from the factory**, meaning the
physical PA14 pin voltage is *ignored* for boot decisions and boot mode is
taken purely from the `nBOOT0` option bit (default: boot from main flash).
So SWCLK on PA14 works exactly like a normal SWD pin with this design as
wired, with no pull resistor needed. Boot-to-system-bootloader is selected
by setting `nBOOT0`/`nBOOT_SEL` via the SWD debugger (e.g.
STM32CubeProgrammer), not a physical strap — unless someone deliberately
sets `nBOOT_SEL=0` later, which would make PA14's pin voltage matter again
at every reset.

**PC14/PC15 (pins 2/3) are also shared with the LSE oscillator**, named
`PC14-OSCX_IN`/`PC15-OSCX_OUT` — also dormant by default: the LSE oscillator
is off out of reset, and these pins only stop behaving as plain GPIO if
firmware sets the `LSEON` bit in `RCC_CSR`, which this design's firmware has
no reason to do (no RTC crystal is fitted here). Left as spare GPIO (NC) as
before, no hardware change needed.

**Pin 20 is a 4-way multi-bonded pin (PB3/PB4/PB5/PB6 share one physical
pad)**: this is a *different* mechanism from PF2-NRST/PA14-BOOT0 above — it's
not option-byte/reset-time special, just one physical pad wired to four GPIO
peripheral inputs, with a `SYSCFG_CFGR3` register picking which one is
"live" (the other three are forced to passive/digital-input internally).
It's an ordinary peripheral register, not a FLASH option byte: no unlock
sequence, fully rewritable at any time, no bricking risk. **D4 (2nd status
LED) is wired here using the PB3 identity** — firmware must select PB3 in
`SYSCFG_CFGR3` (whatever the factory-default selection turns out to be)
before configuring the pin as a GPIO output, or D4 won't respond.

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
| 10 | nRESET | NRST (STM32 PF2-NRST, pin 6 — see MCU section above) |

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
  the expected 21 signal nets (including `/NRST`, `/LED2_CTRL`,
  `/USB_DM_RAW`, `/USB_DP_RAW`, `/VBUS_RAW`) + `+3V3`/`+5V`/`GND`, with
  every remaining "spare"/unused pin explicitly flagged no-connect (verified
  pin-by-pin against the intended design above).
* All 28 components (27 fitted + DNP R6) loaded their real KiCad footprints
  (including the 2 custom ones) and were placed non-overlapping on a board
  with all 44 nets wired from the netlist (`dwm3000_usb_dongle.kicad_pcb`).
  R6 is marked excluded from BOM/position files to match its schematic DNP flag.
* Schematic and PCB were rendered to PDF/SVG/PNG for visual review.
* U3 (USBLC6-2SC6)'s pin table was taken verbatim from its parent symbol
  (`USBLC6-2P6` in the system `Power_Protection.kicad_sym`, extends-flattened
  the same way as DWM3000/DWM1000). Its 4 signal pins are only 2.54mm apart,
  so they're routed out with a short vertical jog (`jog_label()` in
  `gen_sch.py`) rather than straight stubs, to keep the net labels legible.

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
