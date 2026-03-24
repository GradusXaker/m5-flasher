# Bruce Review Notes

Reviewed target:

- `Bruce-m5stack-sticks3.bin`
- Latest release at the time of review: `1.14`

Quick validation:

- Binary opens correctly in `esptool image-info`
- Detected chip: `ESP32-S3`
- Flash mode: `DIO`
- Flash freq: `80m`
- Declared flash size: `8MB`

## What looks good

- Official binaries are easy to discover through GitHub releases
- Single-image flash flow is straightforward for tools like `esptool`
- `M5Stick S3` release asset naming is consistent: `Bruce-m5stack-sticks3.bin`

## What could be improved in the Bruce ecosystem

- `Web flasher` onboarding is still too technical for first-time users
- Device selection would be easier with images and board-specific notes
- The page briefly shows invalid release date state before data loads
- `M5Stick` boot/download steps need clearer visuals and less text-only guidance
- The installer should highlight the recommended firmware for each board automatically

## What this app improves right now

- Direct desktop flashing over serial without browser/WebSerial friction
- Clear `COM`/serial port selection
- Live flash logs and progress bar
- One-click download of the latest Bruce build for supported `M5Stick` profiles
- Persistent last-used settings for faster repeat flashing

## Good next upgrades for this app

- Add firmware inspection panel with parsed `esptool image-info`
- Auto-detect likely `M5Stick` serial adapters and highlight them
- Add pre-flash connectivity test using `esptool chip_id`
- Add drag-and-drop firmware file support
- Add Windows-specific packaged build and installer
- Add board diagrams for `G0`, `GND`, and reset flow
