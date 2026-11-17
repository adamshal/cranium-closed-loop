"""Replay saved physical evidence; no instrument is contacted in CI."""
import hashlib
import json
from pathlib import Path
import unittest
from workbench.analysis import read_edges
from workbench.logic_demo import verify_get_id,exit_code

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/logic-demo-2026-11-16'

class LogicDemoTests(unittest.TestCase):
    def test_original_physical_csv_hash_matches_saved_capture_manifest(self):
        provenance=json.loads((EVIDENCE/'provenance.json').read_text())
        self.assertEqual(hashlib.sha256((EVIDENCE/'digital.csv').read_bytes()).hexdigest(),
                         provenance['original_artifacts_sha256']['digital.csv'])

    def test_independent_replay_reproduces_five_replies_and_saved_timing(self):
        result=verify_get_id(read_edges(EVIDENCE/'digital.csv',[0,1]))
        saved=json.loads((EVIDENCE/'summary.json').read_text())
        self.assertEqual(result,saved['read_only_test'])
        self.assertTrue(result['passed']);self.assertEqual(result['complete_replies'],5)

    def test_missing_response_wire_cannot_pass(self):
        edges=read_edges(EVIDENCE/'digital.csv',[0,1]);edges[1]=[(0,1),(8,1)]
        result=verify_get_id(edges)
        self.assertEqual(result['requests_observed'],5)
        self.assertEqual(result['complete_replies'],0);self.assertFalse(result['passed'])

    def test_missing_request_wire_cannot_pass_from_unsolicited_replies(self):
        edges=read_edges(EVIDENCE/'digital.csv',[0,1]);edges[0]=[(0,1),(8,1)]
        self.assertFalse(verify_get_id(edges)['passed'])

    def test_failed_read_only_verdict_exits_unsuccessfully(self):
        self.assertEqual(exit_code({'status':'signal_activity_recorded','read_only_test':{'passed':False}},True),1)
        self.assertEqual(exit_code({'status':'read_only_uart_test_passed','read_only_test':{'passed':True}},True),0)
        self.assertEqual(exit_code({'status':'failed'},False),1)

if __name__=='__main__':unittest.main()
