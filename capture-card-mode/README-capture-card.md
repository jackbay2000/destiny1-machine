# destiny1-mk — Capture Card Mode

Play Destiny 1 on PC with mouse and keyboard, using a **capture card for video** instead of PS4 Remote Play's built-in stream.

---

## How it works

```
Bungie Servers
      ↕
   Your PS4 ──── HDMI ────▶ Capture Card ────▶ OBS (you watch here)
      ↑
 virtual controller
      ↑
destiny1-mk-capture.py
(your mouse + keyboard)
      ↑
chiaki-ng (minimized — controller forwarding only, no video)
```

### Why chiaki-ng is still needed

Your PC cannot directly plug into the PS4 over USB as a controller — standard PCs only operate as USB hosts (they read devices, they don't act as one). chiaki-ng connects to your PS4 over your local network using Sony's Remote Play protocol and forwards the virtual controller inputs. It's the bridge that makes the PS4 see your keyboard and mouse as a real controller.

**The key difference from the normal mode:** chiaki-ng runs minimized in the background. You never watch its video window. Instead, your PS4's HDMI output goes into your capture card, and OBS displays it on screen — giving you lower latency video, no compression artifacts, and direct access to the full HDMI signal.

### What the capture card replaces

| | Normal (Remote Play) mode | Capture Card mode |
|---|---|---|
| **Video source** | chiaki-ng decodes the stream over the network | Capture card reads HDMI directly from PS4 |
| **Video latency** | ~50–150ms (network + decode) | ~1–10ms (hardware passthrough) |
| **Video quality** | Compressed H.264 over Remote Play | Uncompressed or lightly-compressed HDMI signal |
| **Controller path** | chiaki-ng forwards virtual controller | chiaki-ng forwards virtual controller (same) |
| **chiaki-ng window** | Fullscreen, you watch it | Minimized, you ignore it |

---

## Requirements

- Windows 10 or 11
- Python 3.10+
- A PS4 with Destiny 1, connected to your local network
- A **capture card** connected between your PS4's HDMI out and your PC
- **OBS Studio** (free) — [obsproject.com](https://obsproject.com)
- Both PC and PS4 on **wired ethernet** (strongly recommended)

chiaki-ng and ViGEmBus are downloaded automatically by setup.bat.

---

## Installation

### Step 1 — Run setup

Double-click **setup.bat** in this folder. It will install Python dependencies, the ViGEmBus virtual gamepad driver, and chiaki-ng.

If you already ran setup.bat from the main folder, you can skip this step — everything is already installed.

---

### Step 2 — Enable Remote Play on your PS4

On your PS4:
- Settings → Remote Play Connection Settings → **Enable Remote Play** ✓
- Settings → Account Management → **Activate as Your Primary PS4** ✓
- Settings → Power Save Settings → Set Features Available in Rest Mode → check **Stay Connected to the Internet** and **Enable Turning On PS4 from Network**

This lets chiaki-ng connect to your PS4 for controller forwarding.

---

### Step 3 — Register your PC with chiaki-ng (one-time)

1. Open chiaki-ng from the Start menu
2. Your PS4 should appear automatically. If not, click **Add Console** and enter your PS4's IP address
3. Double-click your PS4 — it will ask you to log in via PSN to get a registration code
4. Complete the PSN login in the browser, paste the redirect URL back into chiaki-ng
5. chiaki-ng will remember your PS4 going forward

---

### Step 4 — Configure chiaki-ng

#### Disable keyboard input (important)
In chiaki-ng: **Settings → Keys → uncheck "Use keyboard as controller"**

Otherwise chiaki-ng will also try to map your keyboard to the PS4, conflicting with this script.

#### Enable background controller events
In chiaki-ng: **Settings → Controllers → check "Background Controller Events"**

This lets chiaki-ng forward controller input even when its window is minimized.

#### Stream settings (optional — since you won't be watching it)
You can set the stream to the lowest resolution and bitrate (e.g. 360p, 1 Mbps) since you're not using the video. This reduces CPU/network overhead while keeping the controller connection alive.

---

### Step 5 — Set up OBS with your capture card

1. Open OBS Studio
2. In the **Sources** panel, click **+** → **Video Capture Device**
3. Name it (e.g. "PS4 Capture") and click OK
4. In the **Device** dropdown, select your capture card
5. Set the resolution and frame rate to match what your PS4 outputs (typically 1080p 60fps or 1080p 30fps)
6. Click OK — you should now see your PS4's output in OBS

**To display fullscreen:**
- Right-click the OBS preview → **Fullscreen Projector (Preview)** → select your monitor

This gives you a zero-latency fullscreen view of the PS4 while keeping all OBS features (recording, streaming, scene switching) available.

---

## Every session

1. Turn on your PS4 and start Destiny 1
2. Connect your PS4's HDMI to the capture card (and capture card to your PC via USB/PCIe)
3. Open OBS — confirm you can see the PS4's output in the preview
4. Open chiaki-ng and double-click your PS4 to start the Remote Play stream
5. **Minimize chiaki-ng** — you don't need to see its window
6. Double-click **run.bat** in this folder — wait for the terminal message
7. Press **F3** to capture the mouse — cursor disappears and your inputs go to the PS4
8. Play normally — watch the game in OBS

To release the mouse (e.g. to alt-tab to another app), press **F3** again. All controller inputs will immediately release when you do.

To quit: press **Ctrl+C** in the terminal window, or close it.

---

## Key Bindings

Same defaults as the main mode:

| Key | Action |
|-----|--------|
| W A S D | Move (left stick) |
| Mouse | Aim (right stick) |
| Left Click | Shoot (R2) |
| Right Click | Aim Down Sights (L2) |
| Space | Jump (Cross) |
| Shift | Sprint (L3 click) |
| C | Crouch (Circle) |
| R | Reload (Square) |
| T | Swap Weapon (Triangle) |
| E | Grenade (R3) |
| G | Super Ability (L1) |
| Q | Shoot + Aim simultaneously (R1) |
| F | Interact (R2) |
| Tab | Map (Touchpad) |
| Esc | Menu (Options) |
| 1 / 2 / 3 / 4 | D-Pad Up / Down / Left / Right |
| **F3** | **Toggle mouse capture** |

Edit **config.json** (auto-created on first run) to change bindings and sensitivity.

---

## Differences from normal mode

**Focus detection is removed.** In the normal mode, the script watches for chiaki-ng's window to be in focus, and pauses inputs if you alt-tab away from it. In capture card mode, you're watching OBS — not chiaki-ng — so that check would always fail. Instead, inputs are active any time **F3 capture is on**, regardless of which window has focus.

This means:
- You can watch the game fullscreen in OBS and play normally
- If you press F3 to release the mouse, all inputs immediately stop
- If you switch apps without pressing F3, inputs will continue — press F3 first before alt-tabbing

---

## Sensitivity Tuning

Edit **config.json**:

```json
"sensitivity": {
    "x": 1.0,
    "y": 1.0,
    "acceleration": 1.0,
    "ads_multiplier": 0.4
}
```

| Setting | What it does |
|---------|-------------|
| `x` / `y` | Look sensitivity. Higher = faster. Tune first. |
| `acceleration` | Power curve. `1.0` = linear. `1.2` = small movements slow, large fast. |
| `ads_multiplier` | Sensitivity while aiming down sights. `0.4` = 40% of normal. |

Starting points by DPI:
- 800 DPI → `x: 1.5, y: 1.5`
- 1600 DPI → `x: 1.0, y: 1.0`
- 3200 DPI → `x: 0.5, y: 0.5`

---

## Troubleshooting

**Controller not working / PS4 not responding to input**
- Make sure chiaki-ng is running and connected to your PS4 (not just open — it must have started the stream)
- Verify "Background Controller Events" is enabled in chiaki-ng Settings → Controllers
- Make sure run.bat was started before or after chiaki-ng connects (either order is fine)
- Re-run setup.bat if ViGEmBus wasn't installed correctly

**No video in OBS**
- Check that the capture card is selected in the Video Capture Device source
- Try unplugging and replugging the HDMI and USB cables
- Make sure the PS4 is outputting to the HDMI port connected to your capture card (not a TV)
- Some capture cards require drivers — check your capture card manufacturer's website

**chiaki-ng can't find your PS4**
- Make sure Remote Play is enabled on PS4 (Step 2)
- Make sure both devices are on the same network
- Try manually entering your PS4's IP: chiaki-ng → Add Console

**Mouse moves but nothing happens in-game**
- chiaki-ng must be connected and the stream must be active (even minimized)
- Check that "Background Controller Events" is on in chiaki-ng

**Inputs continue after alt-tabbing**
- Press F3 to release mouse capture before switching apps. In capture card mode there is no auto-release on focus change.

**Video latency feels high in OBS**
- Try setting OBS output to use "Game Capture" or reduce the preview rendering resolution
- Enable hardware acceleration in OBS Settings → Advanced → Video
- Some capture cards have a "passthrough" HDMI port — if yours does, connect a monitor there for near-zero latency and use OBS only for recording/streaming
