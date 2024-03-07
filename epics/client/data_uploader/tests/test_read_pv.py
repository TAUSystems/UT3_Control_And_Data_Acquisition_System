from __future__ import annotations

import unittest
import subprocess
from pathlib import Path

from p4p.client.thread import Context

class TestReadPV(unittest.TestCase):
    def setUp(self) -> None:
        self.epics_process = subprocess.Popen(
            [str(Path(__file__).parents[3] / 'git/support/areaDetector-R3-12-1/ADSimDetector/iocs/simDetectorIOC/bin/linux-x86_64/simDetectorApp'),
             str(Path(__file__).parent / 'data'/ 'st.cmd'),
            ]
        )
        return super().setUp()
    
    def test_read_pv(self):
        pva = Context('pva')
        image = pva.get("13SIM1:Spectrometer:LowEnergy:PVA:Image")

    def tearDown(self) -> None:
        self.epics_process.terminate()
        return super().tearDown()

if __name__ == "__main__":
    unittest.main()    