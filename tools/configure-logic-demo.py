#!/usr/bin/env python3
"""Select the demo instruments locally; never transmits, flashes or powers a DUT."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workbench.instruments import serial_inventory
from saleae import automation as a

def main():
    with a.Manager.connect(port=10430,connect_timeout_seconds=3) as manager:
        devices=[d for d in manager.get_devices() if not d.is_simulation]
    if len(devices)!=1:raise RuntimeError('Connect exactly one real Saleae and enable its Automation API on port 10430.')
    ports=[p for p in serial_inventory() if p['vid']==0x1366]
    if not ports:raise RuntimeError('Connect the DK debug/J-Link USB cable.')
    print('Real analyzer:',devices[0].device_type)
    for index,port in enumerate(ports,1):print(f"{index}. {port['port']}")
    print('Select the VCOM wired to P0.22/P0.20. The demonstrated DK used its second interface.')
    index=int(input('Serial port number: '))-1
    if not 0<=index<len(ports):raise ValueError('Invalid port selection')
    state=Path(__file__).resolve().parents[1]/'.state';state.mkdir(mode=0o700,exist_ok=True)
    path=state/'logic-demo-config.json'
    path.write_text(json.dumps({'uart_port':ports[index]['port'],'saleae_device_id':devices[0].device_id},indent=2)+'\n')
    path.chmod(0o600)
    print('Saved local selection. No commands sent to the board. Run the read-only demo to verify the physical route.')

if __name__=='__main__':main()
