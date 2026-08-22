# Collar Rev-A — dog-worn puck

Physical device **on the dog** (collar or harness), not a human bracelet.

```bash
./kicad-launcher --run collar
./kicad-launcher --sch status
./kicad-launcher --sch verify
```

| Path | Role |
|------|------|
| `collar-reva.kicad_pro` | KiCad project |
| `collar-reva.kicad_sch` | Root: Power / MCU / Sensors |
| `pins.h` | Firmware GPIO contract (from `scripts/aarf_sch/nets.py`) |
| `DESIGN_SPEC.md` | Power budget, GPIO, floorplan |

Regenerate sheets after editing `nets.py`:

```bash
python3 scripts/aarf_sch/emit_collar_sch.py
```
