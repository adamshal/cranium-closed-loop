"""Offline verdicts for the demonstrated read-only console protocol."""
import re
from .analysis import uart_bytes,uart_lines

def verify_get_id(edges,baud=115200):
    requests=[line for line in uart_lines(uart_bytes(edges[0],baud)) if line[1]==b'GET_ID\n']
    replies=uart_lines(uart_bytes(edges[1],baud))
    results=[]
    pattern=rb'OK [^|\r\n]+\|[0-9]+\.[0-9]+\.[0-9]+[^ \r\n]*\r?\n'
    for i,(_,_,end) in enumerate(requests):
        next_start=requests[i+1][0] if i+1<len(requests) else float('inf')
        actual=[line for line in replies if end<=line[0]<next_start and line[1].strip() not in (b'',b'GET_ID')]
        payload=next((line for line in actual if re.fullmatch(pattern,line[1])),None)
        results.append({'reply_complete':payload is not None,
            'payload_start_latency_ms':round((payload[0]-end)*1000,4) if payload else None})
    return {'command':'GET_ID','requests_observed':len(requests),
        'complete_replies':sum(x['reply_complete'] for x in results),'results':results,
        'passed':len(results)==5 and all(x['reply_complete'] for x in results)}

def exit_code(report,read_only=False):
    if report.get('status')=='failed':return 1
    if read_only and not report.get('read_only_test',{}).get('passed'):return 1
    return 0
