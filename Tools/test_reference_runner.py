"""Regression tests for the runner, using explicitly synthetic subprocess logs.
These unit-test fixtures are NOT evidence of Unreal execution.
"""
from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('runner', Path(__file__).with_name('run_reference.py'))
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class VerificationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir='C:/Users/mrjul/AppData/Local/hermes/cache/scratch',prefix='gallery_runner_test_')
        self.old=runner.LOGS
        self.old_root=runner.ROOT
        runner.LOGS=Path(self.tmp.name)
        runner.ROOT=Path(self.tmp.name)
        self.source=runner.ROOT/'Source/Fixture.cpp'
        self.source.parent.mkdir()
        self.source.write_text('// test fixture, never compiled')
        self.dll=runner.ROOT/'Binaries/Win64/UnrealEditor-IndustrialGallery.dll'
        self.dll.parent.mkdir(parents=True)
        self.dll.write_text('unit-test fixture, NEVER executed')
        os.utime(self.source,(100,100))
        os.utime(self.dll,(200,200))
    def tearDown(self):
        runner.LOGS=self.old
        runner.ROOT=self.old_root
        self.tmp.cleanup()
    def log(self,stage,text):
        return runner.run(stage,[sys.executable,'-c','print('+repr(text)+')'],timeout=10)
    def test_rejects_stale_module_before_engine_launch(self):
        os.utime(self.source,(300,300))
        with self.assertRaises(RuntimeError):
            self.log('probe','ReferenceProbe: result=PASS\nInputProbe: result=PASS')
    def test_rejects_missing_module_before_engine_launch(self):
        self.dll.unlink()
        with self.assertRaises(RuntimeError):
            self.log('probe','ReferenceProbe: result=PASS\nInputProbe: result=PASS')
    def test_rejects_probe_without_input_result(self):
        with self.assertRaises(RuntimeError):
            self.log('probe','ReferenceProbe: grounded=1 collision=1 floor=1 result=PASS')
    def test_rejects_false_overall_pass_after_case_failure(self):
        with self.assertRaises(RuntimeError):
            self.log('probe','ReferenceProbe: result=PASS\nInputProbe: W travel=0 -> FAIL\nInputProbe: result=PASS')
    def test_rejects_input_pass_without_floor_result(self):
        with self.assertRaises(RuntimeError):
            self.log('probe','InputProbe: result=PASS')
    def test_accepts_both_positive_results(self):
        self.log('probe','ReferenceProbe: grounded=1 collision=1 floor=1 result=PASS\nInputProbe: result=PASS')
    def test_rejects_default_material_usage_flag_fallback(self):
        with self.assertRaises(RuntimeError):
            self.log('capture','LogMaterial: Warning: Material M_Wood missing usage flag InstancedStaticMeshes! Default Material will be used in game.')

if __name__=='__main__':
    unittest.main(verbosity=2)
