#!/usr/bin/env python3
"""Render the published physical trace; requires optional matplotlib."""
import bisect
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from workbench.analysis import read_edges,uart_bytes,uart_lines

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'evidence/logic-demo-2026-11-16'
edges=read_edges(folder/'digital.csv',[0,1])
summary=json.loads((folder/'summary.json').read_text())
request=uart_lines(uart_bytes(edges[0]))[0]
reply=next(line for line in uart_lines(uart_bytes(edges[1])) if line[1].startswith(b'OK '))
origin=request[0]
left=origin-.00015
right=reply[2]+.00025
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig,axes=plt.subplots(2,1,figsize=(12,4.8),sharex=True)
fig.patch.set_facecolor('#f6f7f9')
for channel,ax in enumerate(axes):
    times=[t for t,_ in edges[channel]]
    start=max(0,bisect.bisect_right(times,left)-1)
    end=bisect.bisect_right(times,right)
    selected=edges[channel][start:end]
    x=[(t-origin)*1000 for t,_ in selected]+[(right-origin)*1000]
    y=[v for _,v in selected]+[selected[-1][1]]
    ax.step(x,y,where='post',color=('#1b6a8f' if channel==0 else '#197353'),lw=1.3)
    ax.set_yticks([0,1],['Low','High']);ax.set_ylim(-.25,1.65)
    ax.set_ylabel('D0 · Board RX' if channel==0 else 'D1 · Board TX',labelpad=12)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x',color='#dce1e6',lw=.7)
    ax.set_xlim((left-origin)*1000,(right-origin)*1000)
axes[0].axvspan(0,(request[2]-origin)*1000,color='#1b6a8f',alpha=.09)
axes[0].text(.02,1.30,'GET_ID + newline',color='#1b6a8f',weight='bold')
axes[1].axvspan((reply[0]-origin)*1000,(reply[2]-origin)*1000,color='#197353',alpha=.09)
axes[1].text((reply[0]-origin)*1000+.02,1.30,'OK <device-id>|1.19.3+0',color='#197353',weight='bold')
axes[1].text(.03,-.15,'Console echo',fontsize=9,color='#52616b')
axes[0].annotate('',xy=((reply[0]-origin)*1000,1.04),xytext=((request[2]-origin)*1000,1.04),
    arrowprops={'arrowstyle':'<->','color':'#333333'})
axes[0].text((request[2]-origin)*1000+.01,1.27,'0.3414 ms',fontsize=10)
axes[1].set_xlabel('Time from first request start (ms)')
fig.suptitle('CRANIUM  /  Physical UART evidence',x=.08,y=.97,ha='left',weight='bold',fontsize=17)
fig.text(.08,.875,'Recorded Nov 16, 2026 · 4 MHz · 115200 baud 8N1 · First transaction shown',color='#52616b')
fig.text(.08,.035,'Full 8-second capture: 5 requests / 5 valid replies. Maximum payload-start delay: '+
    str(summary['maximum_payload_start_latency_ms'])+' ms. Existing firmware preserved.',fontsize=10)
fig.subplots_adjust(left=.12,right=.98,top=.82,bottom=.17,hspace=.30)
fig.savefig(folder/'waveform.png',dpi=160,facecolor=fig.get_facecolor())
print(folder/'waveform.png')
