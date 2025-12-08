import asyncio
import time
from typing import Sequence

from norman_core.services.persist import Persist
from norman_objects.shared.queries.query_constraints import QueryConstraints
from norman_objects.shared.security.sensitive import Sensitive
from norman_objects.shared.status_flags.status_flag import StatusFlag
from norman_objects.shared.status_flags.status_flag_value import StatusFlagValue

from norman._app_config import NormanAppConfig


class FlagStatusResolver:
    """
    Utility class responsible for polling entity status flags until all
    entities reach a terminal state. This resolver repeatedly checks the
    `Status_Flags` stored in the Persist service and waits until every
    entity reaches the `Finished` state or fails.

    The resolver enforces a configurable timeout and interval between
    polling cycles, both sourced from `NormanAppConfig`.

    **Methods**
    """
    def __init__(self):
        self._persist_service = Persist()
        self._timeout_seconds =  NormanAppConfig.flag_timeout_seconds

    async def wait_for_entities(self, token: Sensitive[str], entity_ids: Sequence[str]) -> None:
        """
        **Coroutine**

        Wait until all specified entities have reached the `Finished` state,
        polling the `Status_Flags` through the Persist service. The method
        terminates early if any entity enters an `Error` state or if the
        operation times out.

        **Parameters**

        - **token** (`Sensitive[str]`)
            Authentication token granting access to Persist service queries.

        - **entity_ids** (`Sequence[str]`)
            Collection of entity identifiers whose status flags should be
            monitored until completion.

        **Returns**

        - **None**
            Returns when all entities have successfully reached the
            `Finished` state.

        **Raises**

        - **ValueError**
            Raised if:
            - No status flags are returned for the provided entities.
            - Any entity transitions into the `Error` state.

        - **TimeoutError**
            Raised if the polling process exceeds the configured timeout
            before all entities reach the `Finished` state.
        """

        flag_constraints = QueryConstraints.includes("Status_Flags", "Entity_ID", list(entity_ids))
        wait_start_time = time.time()
        wait_end_time = wait_start_time + self._timeout_seconds

        while time.time() < wait_end_time:
            iteration_start_time = time.time()

            status_flags = await self._persist_service.status_flags.get_status_flags(token, flag_constraints)
            if status_flags is None:
                raise ValueError("No status flags found for entities")

            flattened_flags = []
            for flag_list in status_flags.values():
                flattened_flags += flag_list

            all_flags_finished = True
            for status_flag in flattened_flags:
                if status_flag.flag_value == StatusFlagValue.Error:
                    raise ValueError("Status flags at error state - One or more entities have failed")
                if status_flag.flag_value != StatusFlagValue.Finished:
                    all_flags_finished = False

            if all_flags_finished:
                return

            loop_iteration_end = time.time()
            iteration_duration = loop_iteration_end - iteration_start_time
            wait_time = NormanAppConfig.get_flags_interval - iteration_duration
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        raise TimeoutError("Status flags did not finish - Timed out waiting for entities")
