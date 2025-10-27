import asyncio
import time
from typing import Iterable, Sequence

from norman_core.services.persist import Persist
from norman_objects.shared.security.sensitive import Sensitive
from norman_objects.shared.queries.query_constraints import QueryConstraints
from norman_objects.shared.status_flags.status_flag import StatusFlag
from norman_objects.shared.status_flags.status_flag_value import StatusFlagValue
from norman._app_config import NormanAppConfig


class FlagHelper:
    def __init__(self):
        self._persist_service = Persist()

    async def wait_for_entities(self, token: Sensitive[str], entity_ids: Sequence[str]) -> None:
        flag_constraints = QueryConstraints.includes("Status_Flags", "Entity_ID", list(entity_ids))

        while True:
            start_time = time.time()
            results = await self._persist_service.status_flags.get_status_flags(token, flag_constraints)
            if not results:
                raise ValueError(f"No status flags found for entities: {entity_ids}")

            all_flags: list[StatusFlag] = [flag for flag_list in results.values() for flag in flag_list]

            any_failed = any(flag.flag_value == StatusFlagValue.Error for flag in all_flags)
            all_finished = all(flag.flag_value == StatusFlagValue.Finished for flag in all_flags)

            if any_failed:
                raise ValueError(f"One or more entities failed: {entity_ids}")

            if all_finished:
                break

            elapsed = time.time() - start_time
            wait_time = NormanAppConfig.get_flags_interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
