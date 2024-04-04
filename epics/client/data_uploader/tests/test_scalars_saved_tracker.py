from __future__ import annotations

import unittest

from data_uploader import ScalarsSavedTracker
from data_uploader.utils.types import ScalarSaveStatus
from measurement_db.orm.tables import Variable, VariableSource, Shot

from typing import NamedTuple
class DummyPV(NamedTuple):
    connected: bool = True

class TestScalarsSavedTracker(unittest.TestCase):
    def setUp(self) -> None:
        self.variables = [
            Variable(name='fetched_variable', source=VariableSource.fetch),
            Variable(name='monitored_variable', source=VariableSource.monitor),
            Variable(name='image_backend_variable', source=VariableSource.image_backend),
        ]
        
        self.shots = [
            Shot(seq=1),
            Shot(seq=2),
        ]

        for variable in self.variables:
            variable.pv = DummyPV()
            variable.dtype = float

        self.scalars_saved_tracker = ScalarsSavedTracker(self.variables, len(self.shots))

        return super().setUp()
    
    def test_init(self):
        self.assertTrue(all(not self.scalars_saved_tracker.all_scalars_ready(ss, vs)
                            for ss in range(1, self.scalars_saved_tracker.number_of_shots + 1)
                            for vs in [VariableSource.fetch, VariableSource.monitor, VariableSource.image_backend]
                       ))


    def test_update(self):
        shot1 = self.shots[0]
        
        self.scalars_saved_tracker.update(self.variables[0], shot1)
        self.assertEqual(self.scalars_saved_tracker.scalar_save_status[0]['fetched_variable'], ScalarSaveStatus.Saved)
        self.scalars_saved_tracker.update(self.variables[1], shot1, ScalarSaveStatus.Error)

        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready(1, VariableSource.fetch))
        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready(1, [VariableSource.fetch]))
        # expect default to be all three of fetch, monitor, and image_backend
        self.assertFalse(self.scalars_saved_tracker.all_scalars_ready(1))

        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready(1, {VariableSource.fetch, VariableSource.monitor}))
        # expect not ready when Saved is the only ready status
        self.assertFalse(self.scalars_saved_tracker.all_scalars_ready(1, {VariableSource.fetch, VariableSource.monitor}, ScalarSaveStatus.Saved))
        self.assertFalse(self.scalars_saved_tracker.all_scalars_ready(1, {VariableSource.fetch, VariableSource.monitor}, {ScalarSaveStatus.Saved}))

        # Finish all variables for shot with seq==1
        self.scalars_saved_tracker.update(self.variables[2], shot1)
        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready(1))

        # try to update a status for shot with seq==1
        # this should delete the cache entry and issue a warning
        self.assertIn((shot1.seq, VariableSource.fetch), self.scalars_saved_tracker.shot_ready_cache)
        self.scalars_saved_tracker.update(self.variables[0], shot1, ScalarSaveStatus.TimedOut)
        self.assertNotIn((shot1.seq, VariableSource.fetch), self.scalars_saved_tracker.shot_ready_cache)

        # finish second shot
        self.assertFalse(self.scalars_saved_tracker.all_scalars_ready([1, 2]))
        for variable in self.variables:
            self.scalars_saved_tracker.update(variable, self.shots[1])
        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready([1, 2]))
        self.assertTrue(self.scalars_saved_tracker.all_scalars_ready())


if __name__ == "__main__":
    unittest.main()
