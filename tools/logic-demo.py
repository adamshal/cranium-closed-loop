#!/usr/bin/env python3
"""Saleae UART demo: passive by default, optional labelled host UART probe."""
import argparse
import datetime as dt
import fcntl
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from saleae import automation as a
from workbench.analysis import read_edges,uart_bytes
from workbench.logic_demo import verify_get_id,exit_code
from workbench.build import ROOT
from workbench.runner import save,artifact_manifest
from workbench.instruments import serial_inventory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=8,choices=range(1,31))
    parser.add_argument('--uart-probe',help='Connected J-Link VCOM port; send five labelled text messages, no firmware changes')
    parser.add_argument('--read-only-demo',action='store_true',help='Use five GET_ID requests supported by existing CRANIUM firmware')
    parser.add_argument('--show',action='store_true',help='Leave the saved capture open in Logic 2')
    parser.add_argument('--presentation',action='store_true',help='Show a concise live demo in the terminal')
    args=parser.parse_args()
    if args.uart_probe=='configured':
        args.uart_probe=json.loads((ROOT/'.state/logic-demo-config.json').read_text())['uart_port']
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    folder=ROOT/'captures'/('logic-demo-'+stamp);folder.mkdir(parents=True)
    report={'started_at':stamp,'status':'running','hardware_passed':False,
            'firmware_written':False,'serial_writes':False,'ppk_used':False,
            'purpose':'Passive observation of existing firmware; no ACK/latency or optimization pass claimed',
            'sample_rate_hz':4000000,'duration_s':args.seconds,'baud_assumption':115200,
            'connections':{'0':'P0.22 / nominal UART0 RX','1':'P0.20 / nominal UART0 TX','ground':'DK GND'}}
    probe=b''.join(f'CRANIUM_LOGIC_DEMO_{i:04d}\n'.encode() for i in range(1,6))
    if args.read_only_demo:
        if not args.uart_probe:parser.error('--read-only-demo requires --uart-probe')
        probe=b'GET_ID\n'*5
    (ROOT/'.state').mkdir(exist_ok=True)
    with (ROOT/'.state/bench.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            if args.uart_probe:
                actual=[p for p in serial_inventory() if p['port']==args.uart_probe and p['vid']==0x1366]
                if len(actual)!=1:raise RuntimeError('UART probe must use a connected J-Link VCOM port')
                if args.seconds<4:raise ValueError('UART probe needs at least four seconds')
                report.update(purpose='Observe labelled host UART bytes; firmware processing/forwarding not established',
                              serial_writes=True,uart_port=args.uart_probe,expected_probe_hex=probe.hex())
                if args.read_only_demo:report['purpose']='Read-only GET_ID request/reply test of existing CRANIUM firmware'
            with a.Manager.connect(port=10430,connect_timeout_seconds=3) as manager:
                devices=[d for d in manager.get_devices() if not d.is_simulation]
                if len(devices)!=1:raise RuntimeError('Expected one real connected Saleae')
                report['device_id']=devices[0].device_id
                configuration=a.LogicDeviceConfiguration(enabled_digital_channels=[0,1],digital_sample_rate=4000000)
                timing=a.CaptureConfiguration(capture_mode=a.TimedCaptureMode(duration_seconds=args.seconds))
                print(f'Capturing real Saleae {devices[0].device_id} for {args.seconds}s...',flush=True)
                with manager.start_capture(device_id=devices[0].device_id,device_configuration=configuration,capture_configuration=timing) as capture:
                    if args.uart_probe:
                        import serial
                        with serial.Serial(args.uart_probe,115200,timeout=.2,write_timeout=1,exclusive=True) as uart:
                            # Nordic enables its physical UART routing on a DTR
                            # edge. Reassert it even if the prior client left it high.
                            uart.dtr=False;time.sleep(.05);uart.dtr=True
                            time.sleep(.5)
                            for number,line in enumerate(probe.splitlines(keepends=True),1):
                                if args.presentation:print(f'  Sending request {number}/5: {line.decode().strip()}',flush=True)
                                uart.write(line);uart.flush();time.sleep(.2)
                    capture.wait()
                    handles=[]
                    for channel in (0,1):
                        try:
                            handles.append(capture.add_analyzer('Async Serial',label=f'D{channel} UART',settings={'Input Channel':channel,'Bit Rate (Bits/s)':115200}))
                        except Exception as error:report.setdefault('analyzer_errors',[]).append(str(error))
                    capture.save_capture(str(folder/'capture.sal'))
                    capture.export_raw_data_csv(directory=str(folder),digital_channels=[0,1])
                    if handles:
                        try:capture.export_data_table(str(folder/'decoded.csv'),analyzers=handles)
                        except Exception as error:report['table_export_error']=str(error)
            edges=read_edges(folder/'digital.csv',[0,1])
            report['channels']={}
            for channel in (0,1):
                item={'transitions':sum(x[1]!=y[1] for x,y in zip(edges[channel],edges[channel][1:]))}
                try:
                    data=bytes(x[1] for x in uart_bytes(edges[channel],115200))
                    item.update(decoded_byte_count=len(data),text_preview=data[:2048].decode('utf-8',errors='replace'))
                    if args.uart_probe:item['contains_exact_host_probe']=probe in data
                    (folder/f'channel-{channel}.bin').write_bytes(data)
                except ValueError as error:item['decode_error']=str(error)
                report['channels'][str(channel)]=item
            report['status']='signal_activity_recorded' if any(c['transitions'] for c in report['channels'].values()) else 'no_signal_activity'
            if args.read_only_demo:
                report['read_only_test']=verify_get_id(edges,115200)
                if report['read_only_test']['passed']:report['status']='read_only_uart_test_passed'
        except Exception as error:report.update(status='failed',error=str(error))
        finally:
            report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
            report['artifacts_sha256']=artifact_manifest(folder)
            save(folder/'report.json',report)
            save(ROOT/'.state/latest-logic-demo.json',{'report':str(folder/'report.json'),**report})
    if args.presentation:
        result=report.get('read_only_test',{})
        print(f"\nRequests measured on D0: {result.get('requests_observed',0)}",flush=True)
        print(f"Complete board replies measured on D1: {result.get('complete_replies',0)}",flush=True)
        print('RESULT: '+('PASS — 5/5 read-only UART transactions' if result.get('passed') else report['status']),flush=True)
        print('Existing firmware preserved. Evidence: '+str(folder),flush=True)
    else:print(json.dumps({'folder':str(folder),**report},indent=2))
    if args.show and (folder/'capture.sal').exists():
        with a.Manager.connect(port=10430,connect_timeout_seconds=3) as manager:
            manager.load_capture(str(folder/'capture.sal'))
        print('Saved capture loaded in Logic 2.',flush=True)
    return exit_code(report,args.read_only_demo)


if __name__=='__main__':raise SystemExit(main())
