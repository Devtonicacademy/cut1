from typing import Dict

from apps.api.app.data import db
from apps.api.app.models.schemas import TrackRecordStats
from apps.api.app.tracking import ledger


class TrackerService:
    """
    Public track record, read from the tamper-evident prediction ledger
    (apps/api/app/tracking/ledger.py). Results are graded automatically from the
    official results feed; there is deliberately no way to enter results by hand.
    """
    def get_public_stats(self) -> TrackRecordStats:
        with db.connect() as conn:
            return ledger.stats(conn)

    def verify(self) -> Dict:
        with db.connect() as conn:
            return ledger.verify_chain(conn)

    def export(self) -> Dict:
        with db.connect() as conn:
            return ledger.export(conn)
