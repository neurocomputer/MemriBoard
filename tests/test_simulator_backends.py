"""Public-Connector command parity and device-state regression checks."""
import copy
from configparser import ConfigParser
import logging
from pathlib import Path
import random
import shutil
import tempfile
import unittest

import numpy as np
from manager.board import Connector
from simulator.src import create_crossbar_array


class BackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = ConfigParser()
        self.config.read('simulator/simulator_settings.ini')
        random.seed(101)
        np.random.seed(101)
        create_crossbar_array(str(self.root/'initial'),32,8)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def replay(self, backend: str, batch: bool = False) -> tuple[list[tuple[float,int,int]],list[tuple[float,float]],object]:
        serial = str(self.root/backend)
        shutil.copyfile(self.root/'initial.cb',serial+'.cb')
        connector = Connector(silent=True,logger=logging.getLogger(__name__),
            cb_type='simulator',board_type='rp5_fpga_python',config=self.config,
            crossbar_serial=serial,task_format='SI',simulator_backend=backend)
        self.assertTrue(connector.open_port())
        results = []
        np.random.seed(202)
        rng = random.Random(203)
        try:
            for i in range(120):
                wl,bl = i%8,i%32
                commands = [
                    dict(mode_flag=7,wl=wl,bl=bl,vol=0.,sign=0,pulse_width=0.,id=i),
                    dict(mode_flag=7,wl=wl,bl=bl,vol=2.,sign=i%2,pulse_width=1e-6*(1+i%3),id=i),
                    dict(mode_flag=9,wl=wl,bl=bl,vol=.05,id=i),
                    dict(mode_flag=10,wl=wl,vol=[rng.choice([0.,.025,.05,.1]) for _ in range(32)],id=0),
                    dict(mode_flag=10,wl=wl,vol=[0.]*32,id=0)]
                for task in commands:
                    results.append(connector.impact(copy.deepcopy(task)))
            # Threshold-crossing MVM must use reference RNG semantics.
            results.append(connector.impact(dict(mode_flag=10,wl=0,vol=[.5]*32,id=0)))
            tasks = [dict(mode_flag=10,wl=i%8,vol=[rng.choice([0.,.025,.05,.1]) for _ in range(32)],id=i) for i in range(192)]
            if batch:
                results.extend(connector.impact_many(copy.deepcopy(tasks)))
            else:
                results.extend(connector.impact(copy.deepcopy(task)) for task in tasks)
            # Mixed read/write batches preserve order via scalar dispatch.
            mixed = [dict(mode_flag=7,wl=0,bl=0,vol=2.,sign=0,pulse_width=1e-6,id=1),tasks[0]]
            results.extend(connector.impact_many(copy.deepcopy(mixed)))
            # Internal inspection is only a test, never the experiment API.
            states = [(c.state_variable,c.last_resistance) for row in connector.interface.crossbar for c in row]
            random_after = np.random.get_state()
        finally:
            self.assertTrue(connector.close_port())
        return results,states,random_after

    def check_backend(self, backend: str, batch: bool = False) -> None:
        reference,states,rng = self.replay('legacy')
        observed,other,other_rng = self.replay(backend,batch=batch)
        self.assertEqual(reference,observed)
        np.testing.assert_allclose(states,other,rtol=2e-13,atol=1e-15)
        np.testing.assert_equal(rng,other_rng)

    def test_cpu(self) -> None:
        self.check_backend('cpu')

    def test_cuda(self) -> None:
        try:
            import torch
        except ImportError:
            self.skipTest('Optional torch is not installed')
        if not torch.cuda.is_available():
            self.skipTest('CUDA unavailable')
        self.check_backend('cuda')
        self.check_backend('cuda',batch=True)

    def test_hardware_rejects_simulator_acceleration(self) -> None:
        with self.assertRaises(ValueError):
            Connector(silent=True,logger=logging.getLogger(__name__),cb_type='real',
                board_type='rp5_fpga_python',simulator_backend='cuda')


if __name__ == '__main__':
    unittest.main()
