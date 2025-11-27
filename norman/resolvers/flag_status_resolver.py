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
    def __init__(self):
        self._persist_service = Persist()
        self._timeout_seconds =  NormanAppConfig.flag_timeout_seconds

    async def wait_for_entities(self, token: Sensitive[str], entity_ids: Sequence[str]) -> None:
        flag_constraints = QueryConstraints.includes("Status_Flags", "Entity_ID", list(entity_ids))
        operation_start = time.time()

        while time.time() < operation_start + self._timeout_seconds:
            loop_iteration_start = time.time()

            results = await self._persist_service.status_flags.get_status_flags(token, flag_constraints)
            if results is None:
                raise ValueError("No status flags found for entities")

            all_flags: list[StatusFlag] = []
            for flag_list in results.values():
                for flag in flag_list:
                    all_flags.append(flag)

            any_flag_failed = any(flag.flag_value == StatusFlagValue.Error for flag in all_flags)
            all_flags_finished = all(flag.flag_value == StatusFlagValue.Finished for flag in all_flags)

            if any_flag_failed:
                raise ValueError("One or more entities failed")

            if all_flags_finished:
                return

            now = time.time()
            iteration_duration = now - loop_iteration_start
            wait_time = NormanAppConfig.get_flags_interval - iteration_duration
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        raise TimeoutError("Timed out waiting for entities")
