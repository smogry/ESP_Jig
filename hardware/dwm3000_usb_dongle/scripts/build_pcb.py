#!/usr/bin/env python3
"""Build an initial (unrouted) .kicad_pcb for the DWM3000 USB dongle:
   places every footprint from the generated netlist onto a board and wires
   up nets exactly as read from the netlist, so KiCad shows the correct
   ratsnest. Placement is a tidy non-overlapping grid grouped by subsystem
   (final placement/routing is layout work left for the user)."""
import re
import pcbnew

NET_FILE = "/home/user/ESP_Jig/hardware/dwm3000_usb_dongle/dwm3000_usb_dongle.net"
OUT_PCB = "/home/user/ESP_Jig/hardware/dwm3000_usb_dongle/dwm3000_usb_dongle.kicad_pcb"
FP_DIRS = {
    "Package_SO": "/usr/share/kicad/footprints/Package_SO.pretty",
    "RF_Module": "/usr/share/kicad/footprints/RF_Module.pretty",
    "Package_TO_SOT_SMD": "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty",
    "Resistor_SMD": "/usr/share/kicad/footprints/Resistor_SMD.pretty",
    "Capacitor_SMD": "/usr/share/kicad/footprints/Capacitor_SMD.pretty",
    "LED_SMD": "/usr/share/kicad/footprints/LED_SMD.pretty",
    "dongle": "/home/user/ESP_Jig/hardware/dwm3000_usb_dongle/dongle.pretty",
}

# ---------------------------------------------------------------------------
# Parse the netlist text (already validated by kicad-cli) into components/nets
# ---------------------------------------------------------------------------

def extract_balanced(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return s[start:i+1]
    raise ValueError("unbalanced")

text = open(NET_FILE, encoding="utf-8").read()

components = {}  # ref -> footprint
values = {}      # ref -> schematic Value (so PCB silkscreen matches, not just the bare footprint name)
i = 0
while True:
    m = re.search(r'\(comp \(ref "([^"]+)"\)', text[i:])
    if not m:
        break
    start = i + m.start()
    ref = m.group(1)
    block = extract_balanced(text, start)
    fm = re.search(r'\(footprint "([^"]+)"\)', block)
    if fm:
        components[ref] = fm.group(1)
    vm = re.search(r'\(value "([^"]*)"\)', block)
    if vm:
        values[ref] = vm.group(1)
    i = start + len(block)

nets = []  # (name, [(ref, pin), ...])
i = 0
while True:
    m = re.search(r'\(net \(code "(\d+)"\) \(name "([^"]*)"\)', text[i:])
    if not m:
        break
    start = i + m.start()
    name = m.group(2)
    block = extract_balanced(text, start)
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)
    nets.append((name, nodes))
    i = start + len(block)

print(f"parsed {len(components)} components, {len(nets)} nets")

# ---------------------------------------------------------------------------
# Grid placement grouped by subsystem (mm)
# ---------------------------------------------------------------------------

placement = {
    # Power supply
    "J1": (25, 30), "U2": (65, 30), "C1": (65, 55), "C2": (85, 55),
    # MCU
    "U1": (150, 55), "C3": (120, 25), "C5": (120, 90),
    "R1": (130, 90), "R2": (150, 90), "R6": (170, 90), "D1": (195, 32), "R3": (195, 18),
    # SWD
    "J2": (150, 130),
    # DWM3000
    "DWM1": (270, 70), "C6": (225, 32), "C7": (245, 32),
    "D2": (320, 32), "R4": (320, 18), "D3": (340, 32), "R5": (340, 18),
}

board = pcbnew.BOARD()
board.SetFileName(OUT_PCB)

# board outline (simple rectangle, rough dongle form factor placeholder)
def add_edge_rect(x1, y1, x2, y2):
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.15))
        board.Add(seg)

add_edge_rect(10, 10, 365, 150)

netmap = {}  # name -> NETINFO_ITEM
def get_net(name):
    if name in ("", None):
        return None
    if name not in netmap:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netmap[name] = ni
    return netmap[name]

footprints = {}
for ref, fp_id in components.items():
    lib_nick, fp_name = fp_id.split(":", 1)
    lib_dir = FP_DIRS[lib_nick]
    fp = pcbnew.FootprintLoad(lib_dir, fp_name)
    if fp is None:
        raise RuntimeError(f"could not load footprint {fp_id} for {ref}")
    fp.SetReference(ref)
    if ref in values:
        fp.SetValue(values[ref])
        if values[ref].upper().startswith("DNP"):
            # KiCad 7.0.11's pcbnew has no direct footprint DNP flag yet;
            # excluding from BOM/pos files is the practical PCB-side
            # equivalent of the schematic symbol's (dnp yes) attribute.
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
    x, y = placement[ref]
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    board.Add(fp)
    footprints[ref] = fp

for name, nodes in nets:
    if not name:
        continue
    ni = get_net(name)
    for ref, pin in nodes:
        fp = footprints.get(ref)
        if fp is None:
            continue
        pad = fp.FindPadByNumber(pin)
        if pad is None:
            print(f"WARNING: pad {pin} not found on {ref} ({components[ref]})")
            continue
        pad.SetNet(ni)

pcbnew.SaveBoard(OUT_PCB, board)
print("wrote", OUT_PCB)
print("footprints placed:", len(footprints))
