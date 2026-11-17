# Chat-driven CRANIUM UART demo

Use the configured physical nRF7002 DK and Saleae to test the existing firmware.
Preserve the installed firmware. Do not run bench run, flash, erase, recover,
PPK2 output commands, or firmware-changing console commands.

Read README.md and the local .state/logic-demo-config.json selection. Confirm
hardware availability through Logic 2's API; reject simulated devices. If the
physical wiring is unknown, ask the person at the bench to confirm it.

Run tools/logic-demo.py --seconds 8 --uart-probe configured --read-only-demo
--presentation --show. Expect five GET_ID requests and five complete replies
of the form OK <device-id>|<version>, observed on the physical UART wires.
A host serial write, echo, idle trace or CI test alone is not success.

On a failure, inspect the saved raw trace and report. Correct the host tooling
or serial selection when the evidence warrants it, then repeat the same test.
Keep actual failed results. Never alter measured bytes or weaken the five-reply
criterion to obtain a pass. Report measured timing without claiming a power,
wireless or full firmware-optimization result.
