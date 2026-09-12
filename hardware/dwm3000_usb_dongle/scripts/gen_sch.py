#!/usr/bin/env python3
"""Generate the DWM3000 USB dongle KiCad 7 schematic (.kicad_sch) by hand,
reusing verbatim symbol definitions copied out of the system KiCad libraries.
"""
import re
import uuid
import math

KICAD_SYM_DIR = "/usr/share/kicad/symbols"
EXTRA_SYM_DIR = "/home/user/ESP_Jig/hardware/dwm3000_usb_dongle/extra_symbols"
OUT_DIR = "/home/user/ESP_Jig/hardware/dwm3000_usb_dongle"
PROJECT_NAME = "dwm3000_usb_dongle"

def new_uuid():
    return str(uuid.uuid4())

# ---------------------------------------------------------------------------
# Extract exact symbol S-expression blocks from the system libraries so pin
# geometry / numbering is guaranteed correct (no hand-transcription errors).
# ---------------------------------------------------------------------------

def extract_symbol_block(filepath, symbol_name):
    text = open(filepath, encoding="utf-8").read()
    needle = f'(symbol "{symbol_name}"'
    start = text.index(needle)
    depth = 0
    i = start
    for i in range(start, len(text)):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                break
    return text[start:i+1]


def reindent(block, indent="    "):
    lines = block.splitlines()
    return "\n".join(indent + l if l.strip() else l for l in lines)


LIB_SOURCES = {
    "RF_Module": ("RF_Module.kicad_sym", ["DWM1000", "DWM3000"]),
    "Regulator_Linear": ("Regulator_Linear.kicad_sym", ["XC6220B331MR"]),
    "Connector": ("Connector.kicad_sym", ["USB_A"]),
    "Connector_Generic": ("Connector_Generic.kicad_sym", ["Conn_02x05_Odd_Even"]),
    "Device": ("Device.kicad_sym", ["R", "C", "LED"]),
    "power": ("power.kicad_sym", ["GND", "+3V3", "+5V"]),
}

def extract_subsymbols(block):
    """Return the list of (name, full_text) nested `(symbol "X_y_z" ...)` bodies
    (the graphics/pin units), skipping the outer symbol's own property lines."""
    out = []
    i = 1  # skip index 0: that's the block's OWN opening "(symbol "..."", not a nested unit
    depth = 0
    # find start of first nested "(symbol " occurring after the outer header
    while True:
        j = block.find('(symbol "', i)
        if j == -1:
            break
        # extract its matching block
        d = 0
        k = j
        for k in range(j, len(block)):
            c = block[k]
            if c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
        out.append(block[j:k+1])
        i = k + 1
    return out


def build_lib_symbols():
    parts = []
    cache = {}  # (fname, sym) -> raw extracted block, for resolving "extends"
    for lib_nick, (fname, symbols) in LIB_SOURCES.items():
        path = fname if fname.startswith("/") else f"{KICAD_SYM_DIR}/{fname}"
        for sym in symbols:
            raw = extract_symbol_block(path, sym)
            cache[sym] = raw
            m = re.search(r'\(extends "([^"]+)"\)', raw)
            if m:
                parent_sym = m.group(1)
                parent_raw = cache.get(parent_sym) or extract_symbol_block(path, parent_sym)
                # keep this symbol's own header/properties (everything up to the
                # first nested "(symbol " sub-block), but splice in the parent's
                # graphics/pin sub-symbols, since a schematic's lib_symbols cache
                # must be fully self-contained (no "extends" allowed there).
                own_head_end = raw.find('(symbol "', raw.find(')') )
                # header = everything before the first nested sub-symbol AND before the closing paren
                first_sub = raw.find('\n    (symbol "')
                if first_sub == -1:
                    first_sub = raw.rfind(')')
                header = raw[:first_sub]
                header = re.sub(r' \(extends "[^"]+"\)', '', header, count=1)
                subsymbols = extract_subsymbols(parent_raw)
                renamed_subs = [s.replace(f'"{parent_sym}_', f'"{sym}_') for s in subsymbols]
                block = header + "\n    " + "\n    ".join(renamed_subs) + "\n  )"
            else:
                block = raw
            # rename the top-level symbol name to "LibNick:SymName"
            block = block.replace(f'(symbol "{sym}"', f'(symbol "{lib_nick}:{sym}"', 1)
            parts.append(reindent(block))
    return "\n".join(parts)


def build_stm32c071_symbol():
    """Hand-emit an old-format (KiCad 7.0-compatible) lib_symbol for
    STM32C071F8Px. The upstream KiCad symbol (extra_symbols/STM32C071F8Px.kicad_sym,
    pulled from the current kicad-symbols master) uses newer generator-10.0
    syntax (show_name/do_not_autoplace/exclude_from_sim etc.) that this
    project's KiCad 7.0.11 cannot parse, so this reproduces the same pin
    table (STM32_PINS) in the same plain style used by the other symbols
    here instead of extracting it verbatim."""
    name = "MCU_ST_STM32C0:STM32C071F8Px"
    lines = [f'  (symbol "{name}" (in_bom yes) (on_board yes)']
    lines.append('    (property "Reference" "U" (at -25.4 23.86 0)')
    lines.append('      (effects (font (size 1.27 1.27)) (justify left))')
    lines.append('    )')
    lines.append('    (property "Value" "STM32C071F8Px" (at 2.54 23.86 0)')
    lines.append('      (effects (font (size 1.27 1.27)) (justify left))')
    lines.append('    )')
    lines.append('    (property "Footprint" "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm" (at -25.4 -21.32 0)')
    lines.append('      (effects (font (size 1.27 1.27)) (justify right) hide)')
    lines.append('    )')
    lines.append('    (property "Datasheet" "https://www.st.com/resource/en/datasheet/stm32c071f8.pdf" (at 0 0 0)')
    lines.append('      (effects (font (size 1.27 1.27)) hide)')
    lines.append('    )')
    lines.append('    (symbol "STM32C071F8Px_0_1"')
    lines.append('      (rectangle (start -22.86 -20.32) (end 22.86 20.32)')
    lines.append('        (stroke (width 0.254) (type default))')
    lines.append('        (fill (type background))')
    lines.append('      )')
    lines.append('    )')
    lines.append('    (symbol "STM32C071F8Px_1_1"')
    for num, (x, y, ang, length, pname) in STM32_PINS.items():
        etype = "power_in" if pname in ("VDD", "VSS") else "bidirectional"
        lines.append(f'      (pin {etype} line (at {x:g} {y:g} {ang}) (length {length:g})')
        lines.append(f'        (name "{pname}" (effects (font (size 1.27 1.27))))')
        lines.append(f'        (number "{num}" (effects (font (size 1.27 1.27))))')
        lines.append('      )')
    lines.append('    )')
    lines.append('  )')
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Pin geometry tables: (pin_number -> (x, y, angle_deg, length, elec_type, name))
# angle: 0=right,90=up,180=left,270=down (library Y-up convention)
# ---------------------------------------------------------------------------

# STM32C071F8Px (TSSOP20) -- pin table taken verbatim from the official KiCad
# symbol (MCU_ST_STM32C0:STM32C071F8Px, ST-generated data, Oct 2024).
# NOTE: this package has NO dedicated NRST pin and NO separate VDDA pin
# (single VDD/VSS supply pair) -- both differ from the STM32F042F6Px this
# replaced. See extra_symbols/STM32C071F8Px.kicad_sym for the source symbol.
STM32_PINS = {
    "1":  (-25.4, 0,      0,   2.54, "PB7/PB8"),
    "2":  (-25.4, 10.16,  0,   2.54, "PC14"),
    "3":  (-25.4, 7.62,   0,   2.54, "PC15"),
    "4":  (0,     22.86,  270, 2.54, "VDD"),
    "5":  (0,     -22.86, 90,  2.54, "VSS"),
    "6":  (-25.4, 15.24,  0,   2.54, "PF2"),
    "7":  (25.4,  15.24,  180, 2.54, "PA0"),
    "8":  (25.4,  12.7,   180, 2.54, "PA1"),
    "9":  (25.4,  10.16,  180, 2.54, "PA2"),
    "10": (25.4,  7.62,   180, 2.54, "PA3"),
    "11": (25.4,  5.08,   180, 2.54, "PA4"),
    "12": (25.4,  2.54,   180, 2.54, "PA5"),
    "13": (25.4,  0,      180, 2.54, "PA6"),
    "14": (25.4,  -2.54,  180, 2.54, "PA7"),
    "15": (25.4,  -5.08,  180, 2.54, "PA8"),
    "16": (25.4,  -7.62,  180, 2.54, "PA11"),
    "17": (25.4,  -10.16, 180, 2.54, "PA12"),
    "18": (25.4,  -12.7,  180, 2.54, "PA13"),
    "19": (25.4,  -15.24, 180, 2.54, "PA14/PA15"),
    "20": (-25.4, 2.54,   0,   2.54, "PB3/PB4/PB5/PB6"),
}

DWM_PINS = {
    "1":  (-22.86, 5.08,   0,   2.54, "EXTON"),
    "2":  (-22.86, 2.54,   0,   2.54, "WAKEUP"),
    "3":  (-22.86, 0,      0,   2.54, "RSTn"),
    "4":  (-22.86, -2.54,  0,   2.54, "GPIO7"),
    "5":  (2.54,   27.94,  270, 2.54, "VDDAON"),
    "6":  (0,      27.94,  270, 2.54, "VDD3V3"),
    "7":  (-2.54,  27.94,  270, 2.54, "VDD3V3"),
    "8":  (0,      -27.94, 90,  2.54, "VSS"),
    "9":  (22.86,  -15.24, 180, 2.54, "GPIO6"),
    "10": (22.86,  -12.7,  180, 2.54, "GPIO5"),
    "11": (22.86,  -10.16, 180, 2.54, "GPIO4"),
    "12": (22.86,  -7.62,  180, 2.54, "GPIO3_TXLED"),
    "13": (22.86,  -5.08,  180, 2.54, "GPIO2_RXLED"),
    "14": (22.86,  -2.54,  180, 2.54, "GPIO1"),
    "15": (22.86,  0,      180, 2.54, "GPIO0"),
    "16": (0,      -27.94, 90,  2.54, "VSS"),
    "17": (22.86,  10.16,  180, 2.54, "SPICSn"),
    "18": (22.86,  12.7,   180, 2.54, "SPIMOSI"),
    "19": (22.86,  15.24,  180, 2.54, "SPIMISO"),
    "20": (22.86,  17.78,  180, 2.54, "SPICLK"),
    "21": (0,      -27.94, 90,  2.54, "VSS"),
    "22": (22.86,  20.32,  180, 2.54, "IRQ"),
    "23": (0,      -27.94, 90,  2.54, "VSS"),
    "24": (0,      -27.94, 90,  2.54, "VSS"),
}

XC6220_PINS = {
    "1": (-12.7, 2.54,  0,   5.08, "VIN"),
    "2": (0,     -10.16,90,  5.08, "GND"),
    "3": (-12.7, -2.54, 0,   5.08, "CE"),
    "4": (7.62,  -2.54, 180, 5.08, "NC"),
    "5": (12.7,  2.54,  180, 5.08, "VOUT"),
}

USB_A_PINS = {
    "1": (7.62,  5.08,  180, 2.54, "VBUS"),
    "2": (7.62,  -2.54, 180, 2.54, "D-"),
    "3": (7.62,  0,     180, 2.54, "D+"),
    "4": (0,     -10.16,90,  2.54, "GND"),
    "5": (-2.54, -10.16,90,  2.54, "Shield"),
}

SWD_PINS = {
    "1":  (-5.08, 5.08,  0,   3.81, "VTref"),
    "2":  (7.62,  5.08,  180, 3.81, "SWDIO"),
    "3":  (-5.08, 2.54,  0,   3.81, "GND"),
    "4":  (7.62,  2.54,  180, 3.81, "SWCLK"),
    "5":  (-5.08, 0,     0,   3.81, "GND"),
    "6":  (7.62,  0,     180, 3.81, "SWO"),
    "7":  (-5.08, -2.54, 0,   3.81, "KEY"),
    "8":  (7.62,  -2.54, 180, 3.81, "NC"),
    "9":  (-5.08, -5.08, 0,   3.81, "GND"),
    "10": (7.62,  -5.08, 180, 3.81, "nRESET"),
}

R_PINS = {"1": (0, 3.81, 270, 1.27, "~"), "2": (0, -3.81, 90, 1.27, "~")}
C_PINS = {"1": (0, 3.81, 270, 2.794, "~"), "2": (0, -3.81, 90, 2.794, "~")}
LED_PINS = {"1": (-3.81, 0, 0, 2.54, "K"), "2": (3.81, 0, 180, 2.54, "A")}
PWR_IN_PIN = {"1": (0, 0, 90, 0, "PWR")}   # generic single power pin @ origin, points up (0 length)

def ang_to_dir(angle):
    a = angle % 360
    return {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[a]

# ---------------------------------------------------------------------------
# Schematic building blocks
# ---------------------------------------------------------------------------

class Schematic:
    def __init__(self):
        self.symbols = []   # instance blocks (text)
        self.wires = []
        self.labels = []
        self.no_connects = []
        self.texts = []

    def place(self, lib_id, ref, value, footprint, pos, pin_table, angle=0, mirror=None,
              ref_offset=(2.0, -2.0), value_offset=(2.0, 2.0), extra_props=None,
              hide_value=False, hide_footprint=True, dnp=False):
        x0, y0 = pos
        uid = new_uuid()
        props = []
        props.append(
            f'(property "Reference" "{ref}" (at {x0+ref_offset[0]:.2f} {y0+ref_offset[1]:.2f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n    )'
        )
        props.append(
            f'(property "Value" "{value}" (at {x0+value_offset[0]:.2f} {y0+value_offset[1]:.2f} 0)\n'
            f'      (effects (font (size 1.27 1.27)){" hide" if hide_value else ""})\n    )'
        )
        props.append(
            f'(property "Footprint" "{footprint}" (at {x0:.2f} {y0:.2f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )'
        )
        props.append(
            f'(property "Datasheet" "" (at {x0:.2f} {y0:.2f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )'
        )
        if extra_props:
            props.extend(extra_props)
        pins = "\n".join(f'    (pin "{num}" (uuid {new_uuid()}))' for num in pin_table)
        instance_path_uuid = new_uuid()
        block = f'''  (symbol (lib_id "{lib_id}") (at {x0:.2f} {y0:.2f} {angle}){" (mirror " + mirror + ")" if mirror else ""}
    (unit 1)
    (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"})
    (uuid {uid})
{chr(10).join("    " + p for p in props)}
{pins}
    (instances
      (project "{PROJECT_NAME}"
        (path "/{ROOT_UUID}"
          (reference "{ref}") (unit 1)
        )
      )
    )
  )'''
        self.symbols.append(block)
        return Instance(x0, y0, angle, mirror, pin_table)

    def wire(self, p1, p2):
        self.wires.append(
            f'  (wire (pts (xy {p1[0]:.2f} {p1[1]:.2f}) (xy {p2[0]:.2f} {p2[1]:.2f}))\n'
            f'    (stroke (width 0) (type default))\n    (uuid {new_uuid()})\n  )'
        )

    def label(self, text, pos, angle=0):
        self.labels.append(
            f'  (label "{text}" (at {pos[0]:.2f} {pos[1]:.2f} {angle})\n'
            f'    (effects (font (size 1.27 1.27)) (justify left bottom))\n'
            f'    (uuid {new_uuid()})\n  )'
        )

    def no_connect(self, pos):
        self.no_connects.append(f'  (no_connect (at {pos[0]:.2f} {pos[1]:.2f}) (uuid {new_uuid()}))')

    def text(self, s, pos, size=2.0):
        self.texts.append(
            f'  (text "{s}" (at {pos[0]:.2f} {pos[1]:.2f} 0)\n'
            f'    (effects (font (size {size} {size})) (justify left))\n'
            f'    (uuid {new_uuid()})\n  )'
        )


class Instance:
    """Computes world-space pin endpoint / stub-end coordinates for a placed part."""
    def __init__(self, x0, y0, angle, mirror, pin_table):
        self.x0, self.y0 = x0, y0
        self.angle = angle
        self.mirror = mirror
        self.pin_table = pin_table

    def _rot(self, x, y):
        # rotate (x,y) by self.angle (schematic-space rotation, CCW positive in KiCad UI
        # but since we only ever use angle=0 in this design we keep it simple)
        a = math.radians(self.angle)
        rx = x * math.cos(a) - y * math.sin(a)
        ry = x * math.sin(a) + y * math.cos(a)
        return rx, ry

    def pin_end(self, num):
        lx, ly, ang, length, name = self.pin_table[num]
        # library Y-up -> schematic Y-down flip
        wx, wy = lx, -ly
        wx, wy = self._rot(wx, wy)
        return (self.x0 + wx, self.y0 + wy)

    def pin_dir(self, num):
        # ang_to_dir(ang) gives the BODY-WARD unit vector in library (Y-up) space
        # (the pin's "at" point is the outer tip, and it extends body-ward by
        # "length" along this vector). The stub must extend OUTWARD instead,
        # i.e. the negation of that vector, then converted to schematic
        # (Y-down) space with the same flip used for positions.
        lx, ly, ang, length, name = self.pin_table[num]
        bx, by = ang_to_dir(ang)
        wx, wy = -bx, by
        wx, wy = self._rot(wx, wy)
        return (wx, wy)

    def stub(self, sch, num, net, stub_len=3.81, label_angle=0, no_conn=False):
        p1 = self.pin_end(num)
        if no_conn:
            sch.no_connect(p1)
            return
        dx, dy = self.pin_dir(num)
        p2 = (p1[0] + dx * stub_len, p1[1] + dy * stub_len)
        sch.wire(p1, p2)
        sch.label(net, p2, label_angle)

    def pwr_stub(self, sch, num, stub_len=2.54):
        """Connect a pin directly (short stub) - caller adds the power symbol separately."""
        p1 = self.pin_end(num)
        dx, dy = self.pin_dir(num)
        p2 = (p1[0] + dx * stub_len, p1[1] + dy * stub_len)
        sch.wire(p1, p2)
        return p2


ROOT_UUID = new_uuid()
sch = Schematic()

# ---------------------------------------------------------------------------
# Place components
# ---------------------------------------------------------------------------

# --- Power supply section ---
J1 = sch.place("Connector:USB_A", "J1", "USB-4AM103AS", "dongle:USB_A_Neltron_5075AR-04",
               (30, 100), USB_A_PINS)
U2 = sch.place("Regulator_Linear:XC6220B331MR", "U2", "XC6220B331MR-G",
               "Package_TO_SOT_SMD:SOT-23-5", (90, 90), XC6220_PINS)
C1 = sch.place("Device:C", "C1", "10uF", "Capacitor_SMD:C_0805_2012Metric", (65, 135), C_PINS)
C2 = sch.place("Device:C", "C2", "10uF", "Capacitor_SMD:C_0805_2012Metric", (125, 135), C_PINS)

# --- MCU section ---
U1 = sch.place("MCU_ST_STM32C0:STM32C071F8Px", "U1", "STM32C071F8P6",
               "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm", (190, 115), STM32_PINS)
C3 = sch.place("Device:C", "C3", "100nF", "Capacitor_SMD:C_0603_1608Metric", (150, 55), C_PINS)
R1 = sch.place("Device:R", "R1", "22R", "Resistor_SMD:R_0603_1608Metric", (145, 135), R_PINS)
R2 = sch.place("Device:R", "R2", "22R", "Resistor_SMD:R_0603_1608Metric", (170, 135), R_PINS)
R6 = sch.place("Device:R", "R6", "DNP 1.5k (see README: only if MCU lacks an internal USB D+ pull-up)",
                "Resistor_SMD:R_0603_1608Metric", (195, 135), R_PINS, dnp=True)
D1 = sch.place("Device:LED", "D1", "LED", "LED_SMD:LED_0603_1608Metric", (225, 45), LED_PINS)
R3 = sch.place("Device:R", "R3", "1k", "Resistor_SMD:R_0603_1608Metric", (225, 25), R_PINS)

# --- SWD programming connector ---
J2 = sch.place("Connector_Generic:Conn_02x05_Odd_Even", "J2", "3221-10-0300-00",
               "dongle:BoxHeader_2x05_P1.27mm_CnCTech_3221", (185, 220), SWD_PINS)

# --- DWM3000 UWB module section ---
DWM1 = sch.place("RF_Module:DWM3000", "DWM1", "DWM3000", "RF_Module:DWM1000",
                  (330, 130), DWM_PINS)
C6 = sch.place("Device:C", "C6", "1uF", "Capacitor_SMD:C_0603_1608Metric", (295, 50), C_PINS)
C7 = sch.place("Device:C", "C7", "100nF", "Capacitor_SMD:C_0603_1608Metric", (325, 50), C_PINS)
D2 = sch.place("Device:LED", "D2", "LED", "LED_SMD:LED_0603_1608Metric", (365, 45), LED_PINS)
R4 = sch.place("Device:R", "R4", "330R", "Resistor_SMD:R_0603_1608Metric", (365, 25), R_PINS)
D3 = sch.place("Device:LED", "D3", "LED", "LED_SMD:LED_0603_1608Metric", (390, 45), LED_PINS)
R5 = sch.place("Device:R", "R5", "330R", "Resistor_SMD:R_0603_1608Metric", (390, 25), R_PINS)

# power symbols (one instance per node placed near where it's needed) -----------
pwr_counter = [0]
def add_power(lib_id, pos):
    pwr_counter[0] += 1
    n = pwr_counter[0]
    x0, y0 = pos
    block = f'''  (symbol (lib_id "power:{lib_id}") (at {x0:.2f} {y0:.2f} 0)
    (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid {new_uuid()})
    (property "Reference" "#PWR0{n}" (at {x0:.2f} {y0+3.0:.2f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "{lib_id}" (at {x0+2.0:.2f} {y0:.2f} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {x0:.2f} {y0:.2f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "" (at {x0:.2f} {y0:.2f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid {new_uuid()}))
    (instances
      (project "{PROJECT_NAME}"
        (path "/{ROOT_UUID}"
          (reference "#PWR0{n}") (unit 1)
        )
      )
    )
  )'''
    sch.symbols.append(block)

def wire_to_power(inst, pin_num, lib_id, stub_len=3.81):
    """Draw a stub from a pin and terminate it with the given power symbol,
    placed exactly at the stub end (power pin is at symbol origin, pointing up)."""
    p1 = inst.pin_end(pin_num)
    dx, dy = inst.pin_dir(pin_num)
    p2 = (p1[0] + dx * stub_len, p1[1] + dy * stub_len)
    sch.wire(p1, p2)
    add_power(lib_id, p2)

def wire_between(pA, numA, pB, numB):
    sch.wire(pA.pin_end(numA), pB.pin_end(numB))

def label_pin(inst, num, net, stub_len=3.81, label_angle=0):
    inst.stub(sch, num, net, stub_len=stub_len, label_angle=label_angle)

def nc_pin(inst, num):
    inst.stub(sch, num, None, no_conn=True)

# ===================== NET WIRING =====================

# ---- Power rails ----
# USB connector
wire_to_power(J1, "1", "+5V")                       # VBUS
label_pin(J1, "2", "USB_DM", stub_len=7.0)          # to R1
label_pin(J1, "3", "USB_DP", stub_len=7.0)          # to R2
wire_to_power(J1, "4", "GND")
wire_to_power(J1, "5", "GND", stub_len=7.0)

# LDO regulator U2: VIN/CE <= +5V (VBUS), GND, VOUT => +3V3
wire_to_power(U2, "1", "+5V")
wire_to_power(U2, "3", "+5V")     # CE tied to VIN -> always enabled
wire_to_power(U2, "2", "GND")
wire_to_power(U2, "5", "+3V3")

# C1 (LDO input cap, VBUS<->GND), C2 (LDO output cap, +3V3<->GND)
wire_to_power(C1, "1", "+5V")
wire_to_power(C1, "2", "GND")
wire_to_power(C2, "1", "+3V3")
wire_to_power(C2, "2", "GND")

# ---- USB series resistors R1 (D-) / R2 (D+) between connector and MCU ----
label_pin(R1, "1", "USB_DM", stub_len=7.0, label_angle=90)
label_pin(R1, "2", "USB_DM_MCU", stub_len=7.0, label_angle=90)
label_pin(R2, "1", "USB_DP", stub_len=7.0, label_angle=90)
label_pin(R2, "2", "USB_DP_MCU", stub_len=7.0, label_angle=90)

# R6: DNP (do-not-populate) external USB D+ pull-up, only stuffed if bring-up
# testing shows the STM32C071's internal D+ pull-up isn't present/sufficient.
wire_to_power(R6, "1", "+3V3")
label_pin(R6, "2", "USB_DP_MCU", stub_len=7.0, label_angle=90)

# ---- STM32 U1 (STM32C071F8Px: no NRST pin, no separate VDDA pin) ----
nc_pin(U1, "2")     # PC14 spare
nc_pin(U1, "3")     # PC15 spare
nc_pin(U1, "6")     # PF2 spare
nc_pin(U1, "11")    # PA4 spare
nc_pin(U1, "15")    # PA8 spare
nc_pin(U1, "20")    # PB3/PB4/PB5/PB6 spare

label_pin(U1, "1", "LED1_CTRL")                     # PB7/PB8 -> LED1 cathode
wire_to_power(U1, "4", "+3V3")                      # VDD
wire_to_power(U1, "5", "GND")                       # VSS
label_pin(U1, "7", "DWM_WAKEUP")                    # PA0
label_pin(U1, "8", "DWM_RSTN")                      # PA1
label_pin(U1, "9", "DWM_IRQ")                       # PA2
label_pin(U1, "10", "SPI_CS")                       # PA3
label_pin(U1, "12", "SPI_SCK")                      # PA5
label_pin(U1, "13", "SPI_MISO")                     # PA6
label_pin(U1, "14", "SPI_MOSI")                     # PA7
label_pin(U1, "16", "USB_DM_MCU", stub_len=7.0)      # PA11 (native USB_DM, no remap needed)
label_pin(U1, "17", "USB_DP_MCU", stub_len=7.0)      # PA12 (native USB_DP, no remap needed)
label_pin(U1, "18", "SWDIO")                        # PA13
label_pin(U1, "19", "SWCLK")                        # PA14/PA15

# C3: single VDD/VSS decoupling cap (this package has no separate VDDA pin)
wire_to_power(C3, "1", "+3V3"); wire_to_power(C3, "2", "GND")

# LED1 status indicator: +3V3 -R3- LED1(A->K) - LED1_CTRL(U1 PB8 sinks)
wire_to_power(R3, "1", "+3V3")
wire_between(R3, "2", D1, "2")   # R3.2 -> LED1 anode(A, pin2)
label_pin(D1, "1", "LED1_CTRL")  # LED1 cathode(K) -> PB8 net

# ---- SWD connector J2 (ARM 10-pin standard) ----
wire_to_power(J2, "1", "+3V3")   # VTref
label_pin(J2, "2", "SWDIO")
wire_to_power(J2, "3", "GND")
label_pin(J2, "4", "SWCLK")
wire_to_power(J2, "5", "GND")
nc_pin(J2, "6")                  # SWO - not present on Cortex-M0+
nc_pin(J2, "7")                  # KEY
nc_pin(J2, "8")                  # TDI - not present on Cortex-M0+ (SWD only)
wire_to_power(J2, "9", "GND")
nc_pin(J2, "10")                 # nRESET - STM32C071F8Px has no NRST pin to wire to

# ---- DWM3000 module ----
nc_pin(DWM1, "1")   # EXTON (device-enable output; not used)
label_pin(DWM1, "2", "DWM_WAKEUP")
label_pin(DWM1, "3", "DWM_RSTN")
nc_pin(DWM1, "4")   # GPIO7 spare
wire_to_power(DWM1, "5", "+3V3")   # VDDAON
wire_to_power(DWM1, "6", "+3V3")   # VDD3V3
wire_to_power(DWM1, "7", "+3V3")   # VDD3V3
wire_to_power(DWM1, "8", "GND")    # VSS
nc_pin(DWM1, "9")   # GPIO6 spare
nc_pin(DWM1, "10")  # GPIO5 spare
nc_pin(DWM1, "11")  # GPIO4 spare
label_pin(DWM1, "12", "TXLED_CTRL")  # GPIO3/TXLED
label_pin(DWM1, "13", "RXLED_CTRL")  # GPIO2/RXLED
nc_pin(DWM1, "14")  # GPIO1 spare
nc_pin(DWM1, "15")  # GPIO0 spare
wire_to_power(DWM1, "16", "GND")
label_pin(DWM1, "17", "SPI_CS")
label_pin(DWM1, "18", "SPI_MOSI")
label_pin(DWM1, "19", "SPI_MISO")
label_pin(DWM1, "20", "SPI_SCK")
wire_to_power(DWM1, "21", "GND")
label_pin(DWM1, "22", "DWM_IRQ")
wire_to_power(DWM1, "23", "GND")
wire_to_power(DWM1, "24", "GND")

# C6 (VDDAON/AON decoupling), C7 (VDD3V3 decoupling)
wire_to_power(C6, "1", "+3V3"); wire_to_power(C6, "2", "GND")
wire_to_power(C7, "1", "+3V3"); wire_to_power(C7, "2", "GND")

# TX/RX activity LEDs driven directly by DWM3000 GPIO pins
wire_to_power(R4, "1", "+3V3")
sch.wire(R4.pin_end("2"), D2.pin_end("2"))
label_pin(D2, "1", "TXLED_CTRL")

wire_to_power(R5, "1", "+3V3")
sch.wire(R5.pin_end("2"), D3.pin_end("2"))
label_pin(D3, "1", "RXLED_CTRL")

# ---- Section titles ----
sch.text("USB / Power Supply (5V -> 3.3V, XC6220B331)", (18, 50), size=2.0)
sch.text("STM32C071F8P6 (Host MCU)", (155, 30), size=2.0)
sch.text("SWD Programming Connector", (155, 195), size=2.0)
sch.text("DWM3000 UWB Module", (295, 15), size=2.0)

# ---------------------------------------------------------------------------
# Emit the .kicad_sch file
# ---------------------------------------------------------------------------

lib_symbols = build_stm32c071_symbol() + "\n" + build_lib_symbols()

sch_text = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A3")
  (title_block
    (title "DWM3000 USB Dongle")
    (date "2026-09-08")
    (rev "A")
    (company "")
  )
  (lib_symbols
{lib_symbols}
  )
{chr(10).join(sch.symbols)}
{chr(10).join(sch.wires)}
{chr(10).join(sch.labels)}
{chr(10).join(sch.no_connects)}
{chr(10).join(sch.texts)}
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''

with open(f"{OUT_DIR}/{PROJECT_NAME}.kicad_sch", "w", encoding="utf-8") as f:
    f.write(sch_text)

print("wrote", f"{OUT_DIR}/{PROJECT_NAME}.kicad_sch")
print("symbols:", len(sch.symbols), "wires:", len(sch.wires), "labels:", len(sch.labels))
