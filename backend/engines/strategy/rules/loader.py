"""
Strategy Rule Loader — Load rules from DB.

In production, rules are imported from Excel by the Node.js team
and stored in the strategies DB table.

File: backend/engines/strategy/rules/loader.py
"""

import logging
from typing import List

from engines.strategy.rules.rules_registry import RuleDefinition, get_all_rules

logger = logging.getLogger("bravola.strategy.rules.loader")


class RuleLoader:
    """
    Loads rules from the database.

    Falls back to built-in rules_registry when DB is unavailable.
    """

    def __init__(self, db_session=None):
        self._session = db_session

    async def load_rules(self) -> List[RuleDefinition]:
        """
        Load active rules.

        In production, this queries the strategy_rules table.
        Currently returns built-in rules.
        """
        if self._session:
            try:
                return await self._load_from_db()
            except Exception as exc:
                logger.warning("Failed to load rules from DB: %s — using built-in", exc)

        return get_all_rules()

    async def _load_from_db(self) -> List[RuleDefinition]:
        """Load rules from PostgreSQL (future implementation)."""
        # TODO: Query strategy_rules table when Node.js team populates it
        logger.info("DB rule loading not yet implemented — using built-in rules")
        return get_all_rules()
