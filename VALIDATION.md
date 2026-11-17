# Validation record

## Demonstrated on November 16, 2026

The chat agent drove the host test tooling directly. A real Saleae Logic 8
recorded the nRF7002 DK's P0.22/P0.20 UART wires. In the representative saved
run, five GET_ID requests and five complete OK id|version replies were decoded
from the physical trace. Firmware version: 1.19.3+0. Baud: 115200 8N1;
sample rate: 4 MHz; capture duration: 8 seconds.

Request-to-payload-start delays (ms): 0.3414, 0.3362, 0.3407, 0.3359, 0.3354.
The longest in this run was 0.3414 ms. Console echoes are excluded. These are
observations of this run, not a worst-case bound.

Evidence: [summary](evidence/logic-demo-2026-11-16/summary.json),
[original digital CSV](evidence/logic-demo-2026-11-16/digital.csv),
[transcript](evidence/logic-demo-2026-11-16/transcript.txt),
[provenance](evidence/logic-demo-2026-11-16/provenance.json).

The agent corrected the selected serial interface, DTR handling and its reply
parser based on observed failures, then reran the hardware test successfully.
Repeated runs were presented in Terminal and Logic 2. The working teammate
firmware was preserved; it was not replaced by this repository's app/ image.

## What the result does not establish

- No full MCU firmware edit, flash and hardware retest was demonstrated.
- No Hapimatic-orchestrated agent session was used for the demonstrated run.
- No PPK2 power capture or measured power reduction was completed.
- GET_ID is not the experimental app/'s C1 CRC/sequence protocol; the 100-frame
  ACK timing and CRC-error requirements remain unverified on hardware.
- This test does not establish BLE delivery or live Pi song-history transfer.

`read_only_test.passed=true` means this five-request console test passed.
`hardware_passed=false` in the original local report refers to the broader
firmware/power HIL acceptance test and remains false. We do not relabel that
broader requirement as complete.

## Software and replay checks

Host tests validate the actual C protocol parser, independent UART decoding,
refusal of simulated/missing hardware, instrument cleanup and the new read-only
verdict. CI also decodes the published original CSV and compares its five
replies and measured timing against the saved summary. This is offline replay
of a past hardware run, not a new hardware run in CI.

All 31 host tests passed locally for this submission, including five new
recorded-trace and failure-verdict checks.

The November 15 alternative firmware build/host-test record is retained in
[historical validation](docs/HISTORICAL-SOFTWARE-VALIDATION.md) and
[evidence/software-validation.json](evidence/software-validation.json).
Its two built Nordic profiles were not flashed in the November 16 demo.
