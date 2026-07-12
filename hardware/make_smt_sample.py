#!/usr/bin/env python3
"""
Picoprobe PCB Panelization Script
==================================
Panelize picoprobe with kikit into a 2x3 grid, generating SMT
production files with process edges.

Panel specs:
  - 2x2 grid (4 boards per panel, max side < 10cm)
  - 5mm frame with 4mm board-to-frame gap
  - Mousebites: dia 0.6mm, pitch 0.8mm
  - Tooling holes x4: dia 2mm, 2.0mm from panel outer edge
  - Fiducials x4: 1mm copper pad, 1.5mm opening, 4.5mm from panel outer edge

Run with KiCad Python:
  "C:\Program Files\KiCad\10.0\bin\python.exe" hardware\make_smt_sample.py

Prerequisite:
  Install kikit in KiCad Python (once):
    "C:\Program Files\KiCad\10.0\bin\python.exe" -m pip install kikit

Output:
  hardware/smt_sample/picoprobe_panel.kicad_pcb

Note: panel kept under 10cm per side for low-cost PCB fab.
"""

import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Path config
# ---------------------------------------------------------------------------
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_DIR = os.path.join(PROJECT_DIR, "hardware")
BOARD_FILE = os.path.join(BOARD_DIR, "picoprobe.kicad_pcb")
OUTPUT_DIR = os.path.join(BOARD_DIR, "smt_sample")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "picoprobe_panel.kicad_pcb")
CONFIG_FILE = os.path.join(OUTPUT_DIR, "panelize.json")

# ---------------------------------------------------------------------------
# Panelize JSON config
#   - 2 rows x 3 cols = 6 boards per panel
#   - 5mm frame, 4mm gap between board and frame
#   - Mousebites on all edges
#   - 4 tooling holes + 4 fiducials
# ---------------------------------------------------------------------------
PANEL_CONFIG = {
    "layout": {
        "type": "grid",
        "rows": 1,
        "cols": 2,
        "hspace": "4mm",
        "vspace": "4mm",
        "rotation": "0deg",
        "alternation": "none",
        "renamenet": "Board_{n}-{orig}",
        "renameref": "{orig}"
    },
    "source": {
        "type": "auto",
        "tolerance": "1mm"
    },
    "tabs": {
        "type": "spacing",
        "hcount": 1,
        "vcount": 1,
        "hwidth": "5mm",
        "vwidth": "5mm",
        "mindistance": "0mm",
        "spacing": "10mm"
    },
    "cuts": {
        "type": "mousebites",
        "drill": "0.6mm",
        "spacing": "0.8mm",
        "offset": "-0.2mm",
        "prolong": "0mm"
    },
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
        "size": "2mm",
        "paste": False,
        "soldermaskmargin": "0mm"
    },
    "fiducials": {
        "type": "4fid",
        "hoffset": "4.5mm",
        "voffset": "4.5mm",
        "coppersize": "1mm",
        "opening": "1.5mm",
        "paste": False
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


# ---------------------------------------------------------------------------
def find_kikit() -> str:
    """Find kikit executable path (supports KiCad Python direct install)"""
    # 1. KiCad Python Scripts dir
    candidate = os.path.join(os.path.dirname(sys.executable), "Scripts", "kikit.exe")
    if os.path.exists(candidate):
        return candidate

    # 2. Same dir as KiCad Python
    candidate = os.path.join(os.path.dirname(sys.executable), "kikit.exe")
    if os.path.exists(candidate):
        return candidate

    # 3. pip --user Scripts dir
    import site
    user_base = site.getuserbase()
    if user_base:
        candidate = os.path.join(user_base, "Scripts", "kikit.exe")
        if os.path.exists(candidate):
            return candidate

    # 4. KiCad 3rdparty Python Scripts
    for ver in ["10.0", "9.0", "8.0"]:
        candidate = os.path.join(
            os.path.expanduser("~"), "Documents", "KiCad", ver,
            "3rdparty", "Python311", "Scripts", "kikit.exe"
        )
        if os.path.exists(candidate):
            return candidate

    # 5. Fallback to PATH
    return "kikit"


def find_kicad_python() -> str:
    """Find KiCad bundled Python (with pcbnew module)"""
    try:
        import pcbnew  # noqa: F401
        return sys.executable
    except ImportError:
        pass

    for c in [
        r"C:\Program Files\KiCad\10.0\bin\python.exe",
        r"C:\Program Files\KiCad\9.0\bin\python.exe",
        r"C:\Program Files\KiCad\8.0\bin\python.exe",
    ]:
        if os.path.exists(c):
            return c

    return None


# ---------------------------------------------------------------------------
def get_board_size(pcb_path: str) -> tuple[float, float, float, float]:
    """
    Parse Edge.Cuts layer from .kicad_pcb, return (min_x, min_y, max_x, max_y).

    Match gr_line and gr_arc segments, collect all coordinates on Edge.Cuts,
    then compute the bounding box.
    """
    with open(pcb_path, "r", encoding="utf-8") as f:
        content = f.read()

    coords = []  # collect (x, y)

    # Split by graphic element: find each top-level gr_line / gr_arc block
    pattern = r'\((gr_line|gr_arc)\s.*?\(layer\s+"Edge\.Cuts"\)'
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(0)
        # Extract start / mid / end coordinates
        for tag in ("start", "mid", "end"):
            m = re.search(rf'\({tag}\s+([\d.]+)\s+([\d.]+)\)', block)
            if m:
                coords.append((float(m.group(1)), float(m.group(2))))

    if not coords:
        raise RuntimeError("Failed to extract board outline from Edge.Cuts layer")

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Picoprobe PCB Panelization — 2x2 grid")
    print("=" * 60)

    # 1. Validate input file
    if not os.path.exists(BOARD_FILE):
        print(f"[ERROR] Source PCB file not found: {BOARD_FILE}")
        sys.exit(1)

    print(f"[INFO] Source: {BOARD_FILE}")

    # 2. Get board outline dimensions
    min_x, min_y, max_x, max_y = get_board_size(BOARD_FILE)
    board_w = max_x - min_x
    board_h = max_y - min_y
    print(f"[INFO] Single board size: {board_w:.2f}mm x {board_h:.2f}mm")

    # 3. Calculate panel dimensions
    framing = PANEL_CONFIG["framing"]
    layout = PANEL_CONFIG["layout"]
    frame_w = 5.0       # framing width (mm)
    hgap_frame = 4.0    # horizontal board-to-frame gap (mm)
    vgap_frame = 2.0    # vertical board-to-frame gap (mm, tight to stay under 10cm)
    rows = layout["rows"]
    cols = layout["cols"]

    panel_w = cols * board_w + (cols - 1) * hgap_frame + 2 * hgap_frame + 2 * frame_w
    panel_h = rows * board_h + (rows - 1) * hgap_frame + 2 * vgap_frame + 2 * frame_w

    print(f"[INFO] Panel layout: {rows}x{cols} = {rows * cols} boards")
    print(f"[INFO] Panel size: ~{panel_w:.2f}mm x ~{panel_h:.2f}mm")

    # 4. Ensure output dir exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 5. Write config file
    print(f"[INFO] Writing config: {CONFIG_FILE}")
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(PANEL_CONFIG, f, indent=4, ensure_ascii=False)

    # Print key config
    cuts = PANEL_CONFIG["cuts"]
    tooling = PANEL_CONFIG["tooling"]
    fiducials = PANEL_CONFIG["fiducials"]
    print(f"[CONFIG] Grid: {rows} rows x {cols} cols, hspace={layout['hspace']}, vspace={layout['vspace']}")
    print(f"[CONFIG] Mousebites: drill={cuts['drill']}, spacing={cuts['spacing']}")
    print(f"[CONFIG] Frame: width=5mm, hspace={framing['hspace']}, vspace={framing['vspace']}")
    print(f"[CONFIG] Tooling: {tooling['type']}, size={tooling['size']}, "
          f"offset=({tooling['hoffset']}, {tooling['voffset']})")
    print(f"[CONFIG] Fiducials: {fiducials['type']}, copper={fiducials['coppersize']}, "
          f"opening={fiducials['opening']}, "
          f"offset=({fiducials['hoffset']}, {fiducials['voffset']})")

    # 6. Check runtime environment
    kicad_python = find_kicad_python()
    if kicad_python and kicad_python != sys.executable:
        print(f"[WARN] Current Python lacks pcbnew module!")
        print(f"[WARN] Run with KiCad Python:")
        print(f'       "{kicad_python}" {os.path.relpath(__file__, PROJECT_DIR)}')
        print(f"[WARN] Continuing anyway (may fail)...")

    # 7. Run kikit panelize
    kikit_exe = find_kikit()
    cmd = [
        kikit_exe,
        "panelize",
        "-p", CONFIG_FILE,
        BOARD_FILE,
        OUTPUT_FILE
    ]

    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=BOARD_DIR,
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode != 0:
        print(f"[ERROR] kikit panelize failed (exit {result.returncode})")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        sys.exit(1)

    # 8. Verify output
    if not os.path.exists(OUTPUT_FILE):
        print(f"[ERROR] Output file not generated: {OUTPUT_FILE}")
        sys.exit(1)

    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[OK] Panelization complete!")
    print(f"[OK] Output: {OUTPUT_FILE}")
    print(f"[OK] File size: {file_size_kb:.1f} KB")
    print(f"[OK] Panel: {rows}x{cols} grid, {rows * cols} boards, "
          f"~{panel_w:.2f}mm x ~{panel_h:.2f}mm")

    if result.stdout:
        print(result.stdout)


if __name__ == "__main__":
    main()
