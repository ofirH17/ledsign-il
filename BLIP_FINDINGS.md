# BLIP LED Sign — Findings, Bugs & Protocol Reference
> Last updated: May 2026

---

## 1. Hardware

| Property | Value |
|---|---|
| Device name | `LED_BLE_e03ab2ab` |
| BLE filter | `namePrefix: 'LED_BLE'` |
| MAC address | `5C:ED:E0:3A:B2:AB` |
| Canvas | 32×32 pixels |
| BLE Service UUID | `000000fa-0000-1000-8000-00805f9b34fb` |
| Write Characteristic | `0000fa02-0000-1000-8000-00805f9b34fb` |
| Notify Characteristic | `0000fa03-0000-1000-8000-00805f9b34fb` |

---

## 2. BLE Protocol — Verified Working

### Send Image
```
Packet layout (little-endian):
[prefix_L, prefix_H]     2 bytes LE  = 2 + len(frame)
[0x02, 0x00, 0x00]       3 bytes     header
[size_0..3]              4 bytes LE  PNG file size
[crc_0..3]               4 bytes LE  CRC32 of PNG
[0x00, 0x01]             2 bytes     save slot = 1
[PNG bytes...]                        full 32×32 PNG
```

**Steps:**
1. Render 32×32 canvas → `toBlob('image/png')` → `arrayBuffer()`
2. Compute `CRC32(pngBytes)`
3. Build packet as above
4. Send in 244-byte chunks using `writeValueWithResponse`
5. Wait for ACK on BLE_NO (timeout 5s) — optional, don't block show command
6. Send show_slot: `[0x07,0x00,0x08,0x80,0x01,0x00,0x01]` via `writeValueWithoutResponse`

### Power Commands
```js
POWER_ON  = [0x05, 0x00, 0x07, 0x01, 0x01]  // writeValueWithoutResponse
POWER_OFF = [0x05, 0x00, 0x07, 0x01, 0x00]  // writeValueWithoutResponse
```

### Other Commands
```js
BRIGHTNESS = [0x05, 0x00, 0x04, 0x80, value]  // value = 5-100
FLIP       = [0x05, 0x00, 0x06, 0x80, 1/0]    // 1=rotated, 0=normal
RESET_v1   = [0x04, 0x00, 0x03, 0x80]         // freeze (from iDotMatrix lib)
RESET_v2   = [0x05, 0x00, 0x04, 0x80, 0x50]   // brightness 80% (from iDotMatrix lib)
```

---

## 3. Bugs Found & Fixed

### Bug 1 — CSS Broken Comment (Anti Gravity)
**File:** `LED_app.html` line 63
**Problem:** `/*` opened but never closed — commented out `.sym-grid` and `.sym-grid.sz-l`, breaking the signs grid layout entirely.
**Fix:** Added closing `*/` to the comment on line 63.

### Bug 2 — Flash Tab Hidden (Anti Gravity)
**File:** `LED_app.html`
**Problem:** `style="display:none;"` left on the `sht-anim` tab element.
**Fix:** Removed the inline style.

### Bug 3 — Stray CSS Fragment (Anti Gravity)
**File:** `LED_app.html` line 97
**Problem:** `214,0,.05);}` — orphaned fragment from a deleted rule, causing CSS parse error.
**Fix:** Deleted the line.

### Bug 4 — POWER_ON Never Sent
**File:** `LED_app.html`
**Problem:** App only ever sent POWER_OFF (`setIdle()`). After Anti Gravity triggered POWER_OFF during testing, the LED entered a stored-image state showing "נהג חדש" and ignoring all new images.
**Fix:** Added `POWER_ON [0x05,0x00,0x07,0x01,0x01]` in two places:
  - After successful BLE connection (`_connectDevice`)
  - On every display activation (`setLive`)

### Bug 5 — ACK Timeout Blocking Show Command
**File:** `LED_app.html`
**Problem:** Show command was inside the ACK await block — if ACK timed out (which it often did), show command never executed and image never appeared.
**Fix:** Wrapped ACK in its own try/catch. Show command always fires regardless of ACK.

### Bug 6 — Hero Canvas Click Blocked by Overlay
**File:** `LED_app.html`
**Problem:** Absolutely-positioned power overlay (`sh-power-ov`) covered the hero canvas and absorbed all clicks. Tapping the canvas did nothing.
**Fix:** Added `onclick="onDisplay()"` to the overlay element when created in `updateHero()`.

---

## 4. The "נהג חדש" Stuck Screen — Root Cause

**What happened:**
Anti Gravity's code sent `POWER_OFF [0x05,0x00,0x07,0x01,0x00]` via `setIdle()` when the user toggled off the display. The LED then reverted to its stored default image (which was "נהג חדש") and ignored all subsequent BLE image commands.

**Why it wasn't noticed at first:**
Anti Gravity managed to briefly change the sign during one test session, but after ~3 seconds it reverted. This is normal behavior — the firmware reverts to stored default when it doesn't receive a keep-alive.

**The keep-alive behavior:**
LED firmware reverts to stored default image ~3 seconds after the last BLE image command. The app now sends a keep-alive every 2 seconds while `isLive=true`.

**Recovery procedure (hardware reset):**
1. Press the physical power button to turn off the LED
2. Wait 10 seconds
3. Power on — the iPIXEL logo will appear
4. The device is now in clean state and will respond to BLE commands

---

## 5. Files

| File | Purpose |
|---|---|
| `LED_app.html` | Main production app (BLIP v2) |
| `led_reset.html` | BLE diagnostic/reset tool — use when LED gets stuck |
| `pixel_editor_2.html` | Standalone 32×32 pixel editor |
| `IPIXEL_REFERENCE.md` | Hardware + protocol reference (verified) |
| `IPIXEL_DESIGN_GUIDELINES.md` | Same content as REFERENCE.md |
| `BLIP_FINDINGS.md` | This file |

---

## 6. Protocol Sources Investigated

| Source | URL | Relevance |
|---|---|---|
| Old working repo | github.com/ofirH17/ledsign-il | Same device, older protocol variant |
| iDotMatrix Python lib | github.com/derkalle4/python3-idotmatrix-library | Different device (IDM- prefix), different protocol |
| IPIXEL_REFERENCE.md | Local file | Authoritative reference for this device |

**Key difference from iDotMatrix library:**
- iDotMatrix uses dynamic chunk size from `max_write_without_response_size`
- iDotMatrix PNG upload has no CRC32
- iDotMatrix has no "show" command — image displays immediately
- Our LED_BLE device requires CRC32 + show command

**Old repo vs current app:**
- Old repo used 20-byte chunks + `writeValueWithoutResponse` + show `[05,00,07,80,01]`
- Current app uses 244-byte chunks + `writeValueWithResponse` + show `[07,00,08,80,01,00,01]`
- Both protocols appear to work after hardware reset

---

## 7. GitHub Recommendation

Web Bluetooth **requires HTTPS**. GitHub Pages provides free HTTPS hosting.

**Recommended setup:**
1. Create repo `blip-led-sign`
2. Push `LED_app.html` as `index.html`
3. Enable GitHub Pages → app accessible at `https://[user].github.io/blip-led-sign`
4. Works on Chrome Android over HTTPS = phone as a real remote control

---

## 8. Keep-Alive Implementation

```js
// Fires every 2 seconds while isLive=true
setInterval(() => {
  if (!isLive || !isConnected || !bleChar || bleBusy) return;
  if (activePresetId) sendPresetBLE(preset);
  else if (activeSymbolId || animActiveId) sendPixelsBLE(pixels);
}, 2000);
```
Started by `setLive()`, stopped by `setIdle()` and `setConnected(false)`.
