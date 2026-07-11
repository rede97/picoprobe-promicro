# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Hardware-only KiCad project — a Raspberry Pi Debug Probe expansion board for the **RP2040 Pro Micro** core module. The board is electrically compatible with the official Raspberry Pi Debug Probe. Flash the official [debugprobe](https://github.com/raspberrypi/debugprobe) firmware onto the Pro Micro and it works identically.

## Key files

- `hardware/picoprobe.kicad_pro` — KiCad project file (entry point)
- `hardware/picoprobe.kicad_sch` — schematic
- `hardware/picoprobe.kicad_pcb` — PCB layout
- `hardware/picoprobe-front.png` / `hardware/picoprobe-back.png` — manually placed PCB renders (not auto-generated)
- `hardware/kicad_pro_micro_rp2040/` — git submodule providing the Pro Micro RP2040 KiCad symbol and footprint

## Git submodule

`hardware/kicad_pro_micro_rp2040` is a git submodule pinned to a specific commit. After cloning:

```bash
git submodule update --init --recursive
```

To update the submodule to latest upstream:

```bash
git submodule update --remote hardware/kicad_pro_micro_rp2040
```

## KiCad auto-backups

`hardware/picoprobe-backups/` contains timestamped `.zip` files auto-created by KiCad during editing. These are not manually managed — add to `.gitignore` if they grow too large.

## Documentation

- `README.md` — English (default shown on GitHub)
- `README_CN.md` — Chinese translation, linked from README.md

Both files should be kept in sync when project details change.
