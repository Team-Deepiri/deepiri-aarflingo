# WSL2 LAN access — status and remaining work

## Symptom

On WSL2 with `networkingMode=mirrored`, the runtime server binds
`0.0.0.0:<port>` and is reachable via `localhost`/`127.0.0.1` from Windows, but
**not** via the real LAN IP — from another device on the network, or even
from Windows itself on the same box.

## Root cause (confirmed)

Mirrored-mode inbound socket sharing can fail to forward LAN traffic into
WSL, independent of the app, the port, or firewall config. Diagnosed via:

- Classic Windows Defender Firewall: an inbound-allow rule for the target
  port (`Any` profile) existed, and the active network profile's default
  inbound action had no competing block rule.
- Hyper-V Firewall (the separate layer that gates mirrored-mode VM/WSL
  traffic): the same allow rule is present and enabled there too.
- Isolation test: started a throwaway `python3 -m http.server` on an unused
  port with **no firewall rule of any kind** attached. From Windows itself,
  `http://localhost:<port>` succeeded and `http://<lan-ip>:<port>` timed out.
  No rule exists to block that port, so this rules out firewall configuration
  entirely — Windows was not mirroring the inbound LAN-facing socket into
  WSL at the OS level.
- A separate, unrelated pre-existing app on the same machine showed the
  identical symptom (reachable on localhost, not over LAN), pointing at a
  machine/mode-level issue rather than something specific to this app.

This lines up with a known class of WSL2 mirrored-mode issue where active
VPN/virtual network adapters can interfere with mirrored networking's
inbound path. Not yet root-caused to a specific adapter or to mirrored mode
itself — see "Open questions" below.

## What was fixed in code (`services/runtime/app/platform.py`)

- Added `windows_lan_ip()`: queries Windows directly (`Get-NetIPAddress`)
  for the IP bound to whichever interface owns the default route, rather
  than guessing from adapter names or WSL's own interface list. This is
  environment-agnostic — it works regardless of what VPNs or virtual
  adapters are present, since those aren't the default-route interface.
  Previously `wsl_primary_ip()` was used for this purpose and could return a
  WSL-internal gateway address instead of the real LAN IP — confirmed by
  reproduction: the portproxy was initially misconfigured with the wrong
  listen address as a direct result.
- `_ensure_portproxy` now takes explicit `listen_addr`/`connect_addr`
  instead of hardcoding NAT-mode assumptions, and gained an elevated retry
  path (`_ensure_portproxy_elevated`), matching the existing firewall-rule
  elevation pattern.
- `ensure_lan_access` now runs a portproxy step for **both** NAT and mirrored
  modes:
  - NAT: `0.0.0.0:<port> → <wsl-ip>:<port>` (unchanged behavior).
  - Mirrored: `<real-lan-ip>:<port> → 127.0.0.1:<port>`, on the theory that
    loopback forwarding works even when direct LAN mirroring doesn't.

This is verified correct in isolation (portproxy rule registers with the
right addresses, firewall allows it at both layers) but does not by itself
guarantee LAN access on every machine — on setups where mirrored mode's LAN
forwarding is broken at the OS level, the failure sits below where a
Windows-side portproxy can intervene. It's a real fix for the case where
mirrored mode's LAN forwarding works but the app was proxying to the wrong
listen IP, and a safe no-op attempt otherwise.

## Remaining work / open questions

1. **Not yet root-caused which specific thing breaks mirrored LAN forwarding**
   on affected machines. Candidates, cheapest to test first:
   - Temporarily disable any active VPN/virtual network adapters and retest
     LAN-IP reachability from Windows itself.
   - Confirm `wsl --shutdown` was actually run after `networkingMode=mirrored`
     was set in `.wslconfig` (a stale WSL instance can silently keep running
     the old network mode).
2. **NAT-mode fallback not yet applied anywhere.** Switching
   `networkingMode=nat` in `.wslconfig` is the documented-reliable path and
   the existing NAT-mode portproxy code already handles it, but this
   requires `wsl --shutdown` (kills any running WSL shells/sessions) and
   is disruptive enough mid-session that it needs an explicit go-ahead
   rather than being automated.
3. If NAT mode is chosen on an affected machine, re-verify: firewall rule,
   portproxy entry, and an actual remote-device connection test (not just a
   same-box `Test-NetConnection`).
