#!/usr/bin/env python3
"""
Picoprobe + tiny232 Combined Panelization
==========================================
Merge two boards side-by-side with 3 bridge connections (6x4mm each),
then add SMT frame/mousebites/tooling/fiducials via kikit.

Run: "C:\Program Files\KiCad\10.0\bin\python.exe" hardware\make_combined_panel.py
Output: hardware/smt_sample/picoprobe_tiny232_panel.kicad_pcb
"""

import json
import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_DIR = os.path.join(PROJECT_DIR, "hardware")
PICOPROBE_FILE = os.path.join(BOARD_DIR, "picoprobe.kicad_pcb")
TINY232_FILE = r"C:\Users\rede\tinyboard-tools\hardware\tiny232.kicad_pcb"
OUTPUT_DIR = os.path.join(BOARD_DIR, "smt_sample")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "picoprobe_tiny232_panel.kicad_pcb")
MERGED_FILE = os.path.join(OUTPUT_DIR, "_merged.kicad_pcb")
CONFIG_FILE = os.path.join(OUTPUT_DIR, "panelize_combined.json")


def find_kicad_python():
    for ver in ["10.0", "9.0", "8.0"]:
        p = rf"C:\Program Files\KiCad\{ver}\bin\python.exe"
        if os.path.exists(p):
            return p
    return None


def find_kikit():
    """Find kikit executable path"""
    p = os.path.join(os.path.dirname(sys.executable), "Scripts", "kikit.exe")
    if os.path.exists(p):
        return p
    p = os.path.join(os.path.dirname(sys.executable), "kikit.exe")
    if os.path.exists(p):
        return p
    import site
    user_base = site.getuserbase()
    if user_base:
        p = os.path.join(user_base, "Scripts", "kikit.exe")
        if os.path.exists(p):
            return p
    for ver in ["10.0", "9.0", "8.0"]:
        p = os.path.join(os.path.expanduser("~"), "Documents", "KiCad", ver,
                         "3rdparty", "Python311", "Scripts", "kikit.exe")
        if os.path.exists(p):
            return p
    return "kikit"


def add_bridge_lines(board, layer_id, x, y1, y2, gap):
    """Add Edge.Cuts lines forming a bridge rectangle filling the gap between boards."""
    import pcbnew
    half = gap // 2
    w = 50000  # 0.05mm Edge.Cuts default
    # left vertical
    l1 = pcbnew.PCB_SHAPE()
    l1.SetShape(pcbnew.S_SEGMENT)
    l1.SetLayer(layer_id)
    l1.SetStart(pcbnew.VECTOR2I(int(x - half), int(y1 - w)))
    l1.SetEnd(pcbnew.VECTOR2I(int(x - half), int(y2 + w)))
    l1.SetWidth(w)
    board.Add(l1)
    # right vertical
    l2 = pcbnew.PCB_SHAPE()
    l2.SetShape(pcbnew.S_SEGMENT)
    l2.SetLayer(layer_id)
    l2.SetStart(pcbnew.VECTOR2I(int(x + half), int(y1 - w)))
    l2.SetEnd(pcbnew.VECTOR2I(int(x + half), int(y2 + w)))
    l2.SetWidth(w)
    board.Add(l2)
    # top horizontal
    l3 = pcbnew.PCB_SHAPE()
    l3.SetShape(pcbnew.S_SEGMENT)
    l3.SetLayer(layer_id)
    l3.SetStart(pcbnew.VECTOR2I(int(x - half), int(y1)))
    l3.SetEnd(pcbnew.VECTOR2I(int(x + half), int(y1)))
    l3.SetWidth(w)
    board.Add(l3)
    # bottom horizontal
    l4 = pcbnew.PCB_SHAPE()
    l4.SetShape(pcbnew.S_SEGMENT)
    l4.SetLayer(layer_id)
    l4.SetStart(pcbnew.VECTOR2I(int(x - half), int(y2)))
    l4.SetEnd(pcbnew.VECTOR2I(int(x + half), int(y2)))
    l4.SetWidth(w)
    board.Add(l4)


def main():
    kicad_py = find_kicad_python()
    if not kicad_py:
        print("[ERROR] KiCad Python not found")
        sys.exit(1)
    if kicad_py != sys.executable:
        subprocess.run([kicad_py, __file__])
        sys.exit()

    import pcbnew
    from kikit.panelize import Panel, Origin
    from kikit.units import mm
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union

    print("=" * 60)
    print("Picoprobe + tiny232 Combined Panelization")
    print("=" * 60)

    for f in (PICOPROBE_FILE, TINY232_FILE):
        if not os.path.exists(f):
            print(f"[ERROR] Not found: {f}")
            sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    BRIDGE_GAP = int(4 * mm)  # desired edge-to-edge gap

    # --- measure board sizes ---
    pane = Panel(MERGED_FILE)
    s1 = pane.appendBoard(PICOPROBE_FILE, pcbnew.VECTOR2I(0, 0),
                          origin=Origin.Center, inheritDrc=False)
    s2 = pane.appendBoard(TINY232_FILE, pcbnew.VECTOR2I(0, 0),
                          origin=Origin.Center, inheritDrc=False)
    w1, h1 = s1.GetWidth(), s1.GetHeight()
    w2, h2 = s2.GetWidth(), s2.GetHeight()
    print(f"[INFO] picoprobe: {w1/mm:.1f}x{h1/mm:.1f}mm")
    print(f"[INFO] tiny232:   {w2/mm:.1f}x{h2/mm:.1f}mm")

    # --- place boards with exact gap ---
    total_w = w1 + BRIDGE_GAP + w2
    x1 = -total_w // 2 + w1 // 2
    x2 = x1 + w1 // 2 + BRIDGE_GAP + w2 // 2
    max_h = max(h1, h2)

    pane = Panel(MERGED_FILE)
    pane.appendBoard(PICOPROBE_FILE, pcbnew.VECTOR2I(x1, 0),
                     origin=Origin.Center, inheritDrc=False)
    pane.appendBoard(TINY232_FILE, pcbnew.VECTOR2I(x2, 0),
                     origin=Origin.Center, inheritDrc=False)

    # Measure ACTUAL gap from substrate edges
    s_left = pane.substrates[0].substrates
    s_right = pane.substrates[1].substrates
    left_bounds = s_left.bounds
    right_bounds = s_right.bounds
    print(f"[INFO] left  bounds: {left_bounds[0]/mm:.2f} {left_bounds[1]/mm:.2f} "
          f"{left_bounds[2]/mm:.2f} {left_bounds[3]/mm:.2f}")
    print(f"[INFO] right bounds: {right_bounds[0]/mm:.2f} {right_bounds[1]/mm:.2f} "
          f"{right_bounds[2]/mm:.2f} {right_bounds[3]/mm:.2f}")

    left_right = left_bounds[2]
    right_left = right_bounds[0]
    actual_gap = int(right_left - left_right)
    print(f"[INFO] Actual board-to-board gap: {actual_gap/mm:.2f}mm")

    # --- add bridges: 6mm tall, fill gap, 3 total ---
    edge_layer = pane.board.GetLayerID("Edge.Cuts")
    mid_x = int(left_right + actual_gap // 2)
    bw_v = int(3 * mm)          # half-height: 6mm total per bridge
    bridge_pitch = int(11 * mm)  # 6mm bridge + 5mm spacing
    cy_list = [bridge_pitch, 0, -bridge_pitch]

    for i, cy in enumerate(cy_list):
        y1 = int(cy - bw_v)
        y2 = int(cy + bw_v)
        add_bridge_lines(pane.board, edge_layer, mid_x, y1, y2, actual_gap)
        print(f"  bridge {i+1}: x={mid_x/mm:.1f}, gap={actual_gap/mm:.2f}mm, "
              f"y={y1/mm:.1f}..{y2/mm:.1f}")

    # Merge substrates with bridge polygons
    merged = unary_union([s.substrates for s in pane.substrates])
    for cy in cy_list:
        y1 = int(cy - bw_v)
        y2 = int(cy + bw_v)
        merged = unary_union([merged, sbox(left_right, y1, right_left, y2)])
    pane.boardSubstrate.substrates = merged

    pane.save()
    print(f"[INFO] Merged: {MERGED_FILE}")
    combined_w = (right_bounds[2] - left_bounds[0]) / mm
    combined_h = (max(right_bounds[3], left_bounds[3]) - min(right_bounds[1], left_bounds[1])) / mm
    print(f"[INFO] Combined outline: {combined_w:.1f}x{combined_h:.1f}mm")

    # --- kikit panelize: 1x1 frame only (no internal tabs/cuts) ---
    config = {
        "layout": {
            "type": "grid",
            "rows": 1,
            "cols": 1,
            "hspace": "0mm",
            "vspace": "0mm",
            "renamenet": "Board_{n}-{orig}",
            "renameref": "{orig}"
        },
        "source": {"type": "auto", "tolerance": "1mm"},
        "tabs": {"type": "fixed", "hwidth": "5mm", "vwidth": "5mm",
                 "hcount": 3, "vcount": 2},
        "cuts": {"type": "mousebites", "drill": "0.6mm", "spacing": "0.8mm",
                 "offset": "-0.2mm", "prolong": "0mm"},
        "framing": {
            "type": "frame",
            "hspace": "4mm",
            "vspace": "2mm",
            "width": "5mm",
            "cuts": "both"
        },
        "tooling": {
            "type": "4hole",
            "hoffset": "2.0mm",
            "voffset": "2.0mm",
            "size": "2mm"
        },
        "fiducials": {
            "type": "4fid",
            "hoffset": "4.5mm",
            "voffset": "4.5mm",
            "coppersize": "1mm",
            "opening": "1.5mm"
        },
        "post": {
            "type": "auto",
            "copperfill": False,
            "reconstructarcs": False,
            "millradius": "0mm",
            "origin": "tl",
            "refillzones": False,
            "dimensions": False
        }
    }

    kikit_exe = find_kikit()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"[INFO] Config: {CONFIG_FILE}")

    cmd = [kikit_exe, "panelize", "-p", CONFIG_FILE, MERGED_FILE, OUTPUT_FILE]
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"[ERROR] kikit failed (exit {result.returncode})")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        sys.exit(1)

    if os.path.exists(OUTPUT_FILE):
        size_kb = os.path.getsize(OUTPUT_FILE) / 1024
        print(f"[OK] {OUTPUT_FILE} ({size_kb:.0f} KB)")
    else:
        print("[ERROR] Output not generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
