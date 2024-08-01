from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING
from collections import defaultdict
from operator import attrgetter

from .utils.types import ScalarSaveStatus, ShotSeq

if TYPE_CHECKING:
    from measurement_db.orm.tables import Shot, Variable, VariableSource

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

class ScalarsSavedTracker:
    """ An object to keep track of saved-to-db status of variables for each shot

    Provides all_scalars_ready() method which checks whether all variables for a 
    given shot or set of shots are ready (what "ready" means can be customized)

    Typical workflow is: 
        scalars_saved_tracker = ScalarsSavedTracker(variables)
        for variable in variables:
            try:
                # do stuff to save a measurement to a database
                scalars_saved_tracker.update(variable, shot)
            except:
                scalars_saved_tracker.update(variable, shot, ScalarSaveStatus.Error)
        
        # check if all shots up to now are ready. 
        if scalars_saved_tracker.all_scalars_ready(range(1, shot.seq + 1)):
            # do stuff
    
    """
    def __init__(self, variables: Iterable[Variable], cache_ready_shots: bool = True):
        """ 
        Parameters
        ----------
        variables : list[Variable]
        cache_ready_shots : bool
            Whether to cache shots that are ready, separated by source (and 
            by set of allowed statuses). If it's possible for a shot complete 
            result to revert, set to False. 
        """
        if len(variables) == 0:
            raise ValueError("There should be at least one variable to track.")
        
        self.variables: list[Variable] = list(variables)
        self.cache_ready_shots: bool = cache_ready_shots

        # separate list of Variables by source
        self.variables_by_source: defaultdict[VariableSource, list[Variable]] = defaultdict(list)
        for variable in variables:
            self.variables_by_source[variable.source].append(variable)

        # This is the main directory of scalar save status by shot number and 
        # variable. 
        # Referencing a yet unknown shot seq initializes it with a dict of 
        # ScalarSaveStatus.Waiting for all variables. Note that this dict is 
        # newly created every time (otherwise every shot would have a reference 
        # to the same variables dict)
        def initial_scalar_save_status_for_shot():
            return {variable.name: ScalarSaveStatus.Waiting
                    for variable in variables
                   }
        self.scalar_save_status: defaultdict[ShotSeq, dict[str, ScalarSaveStatus]] = defaultdict(initial_scalar_save_status_for_shot)

        # cache shots that are ready for a given variable source and set of allowed
        # statuses
        # it's a dict of set so that we can check against (shot_seq, variable_source) as well as (shot_seq, variable_source, ready_status_tuple)
        self.shot_ready_cache: defaultdict[tuple[ShotSeq, VariableSource], set[tuple[ScalarSaveStatus]]] = defaultdict(set)

    def update(self, variable: Variable, shot: Shot, status: ScalarSaveStatus = ScalarSaveStatus.Saved):
        """ Set new save status of a variable for a given shot_seq

        Parameters
        ----------
        variable : Variable
        shot : Shot
        status : ScalarSaveStatus
            default is Saved
        """
        self.scalar_save_status[shot.seq][variable.name] = status

        # if this updated a shot/variable_source combination which we have 
        # previously cached as ready (for some set of ready_statuses), remove it
        # from cache and issue a warning.
        if self.cache_ready_shots and ((shot.seq, variable.source) in self.shot_ready_cache):
            del self.shot_ready_cache[(shot.seq, variable.source)]
            logging.warning("Updating status of a shot and variable whose shot/variable "
                            "combination had already been marked as ready for at "
                            "least some result_status set."
                           )

    def all_scalars_ready(self, 
                          shot_seq: ShotSeq | Iterable[ShotSeq],
                          variable_sources: Optional[VariableSource | Iterable[VariableSource]] = None,
                          ready_statuses: ScalarSaveStatus | Iterable[ScalarSaveStatus] = {ScalarSaveStatus.Saved, ScalarSaveStatus.NotExpecting, ScalarSaveStatus.Error, ScalarSaveStatus.TimedOut},
                         ) -> bool:
        """ Returns whether all scalars are ready for one or more shots

        Parameters
        ----------
        shot_seq : ShotSeq | Iterable[ShotSeq]
            one-indexed shot number, or list of shot numbers
        variable_sources : VariableSource | Iterable[VariableSource], optional
            Check only variables that are fetched, monitored, or image_backend, or 
            combination thereof.
            By default all sources
        ready_statuses : ScalarSaveStatus | list[ScalarSaveStatus], optional
            Which save statuses to consider ready. 
            By default all except Waiting: [Saved, NotExpecting, Error, TimedOut]
        
        """

        if variable_sources is None:
            variable_sources = list(self.variables_by_source.keys())

        # for list or range of shot seq numbers, just recursively check each shot
        if isinstance(shot_seq, Iterable):
            return all(self.all_scalars_ready(ShotSeq(ss), variable_sources=variable_sources, ready_statuses=ready_statuses) 
                       for ss in shot_seq
                      )

        if isinstance(variable_sources, Iterable):
            return all(self.all_scalars_ready(shot_seq, variable_sources=vs, ready_statuses=ready_statuses)
                       for vs in variable_sources
                      )

        # make ready_statuses a list if it's a scalar
        if not isinstance(ready_statuses, Iterable):
            ready_statuses = [ready_statuses]

        # at this point, shot_seq is a scalar ShotSeq, and variable_sources is a
        # scalar VariableSource
        assert isinstance(shot_seq, int), f"ScalarsSavedTracker.all_scalars_ready: shot_seq is not an int but {type(shot_seq)}."
        assert isinstance(variable_sources, VariableSource), f"ScalarsSavedTracker.all_scalars_ready: variable_sources is not a VariableSource but {type(variable_sources)}."

        # look in cache to see whether this shot/variable_source combination is 
        # ready
        if self.cache_ready_shots:
            shot_variable_source_cache_key = (shot_seq, variable_sources)
            ready_statuses_cache_key = tuple(sorted(ready_statuses, key=attrgetter('value')))

            if (    shot_variable_source_cache_key in self.shot_ready_cache 
                and ready_statuses_cache_key in self.shot_ready_cache[shot_variable_source_cache_key]
               ):
                return True

        # finally check the directory
        ready = all(self.scalar_save_status[shot_seq][variable.name] in ready_statuses
                    for variable in self.variables_by_source[variable_sources]
                   )
        
        # update cache if we found a ready shot/variable_source combination (for 
        # given ready_statuses)
        if ready and self.cache_ready_shots:
            self.shot_ready_cache[shot_variable_source_cache_key].add(ready_statuses_cache_key)

        return ready


    def highest_seq_all_scalars_ready(self, 
                                      variable_sources: Optional[VariableSource | Iterable[VariableSource]] = None,
                                      ready_statuses: ScalarSaveStatus | Iterable[ScalarSaveStatus] = {ScalarSaveStatus.Saved, ScalarSaveStatus.NotExpecting, ScalarSaveStatus.Error, ScalarSaveStatus.TimedOut},
                                     ) -> ShotSeq:
        """ Return highest seq for which all of (1..seq) are ready

        Returns 0 if scalars aren't ready for shot with seq = 1.

        Parameters
        ----------
        variable_sources : VariableSource | Iterable[VariableSource], optional
            Check only variables that are fetched, monitored, or image_backend, or 
            combination thereof.
            By default all sources
        ready_statuses : ScalarSaveStatus | list[ScalarSaveStatus], optional
            Which save statuses to consider ready. 
            By default all except Waiting: [Saved, NotExpecting, Error, TimedOut]
        
        """

        if variable_sources is None:
            variable_sources = list(self.variables_by_source.keys())

        highest_seq: ShotSeq = 0
        while True:
            # currently checking highest_seq + 1
            shot_seq = highest_seq + 1
            
            # if this shot hasn't even been registered in the directory, deem it
            # not ready and exit
            if shot_seq not in self.scalar_save_status:
                break

            # if this shot isn't ready, exit
            if not self.all_scalars_ready(shot_seq, variable_sources, ready_statuses):
                break

            # all shots up to shot_seq are ready.
            highest_seq = shot_seq

        return highest_seq
