"""
GIS & Spatial Data Module.
Handles place hierarchy parsing, coordinates, distance calculations (Haversine formula), and family migration trails.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.schema import PersonModel, EventModel, PlaceModel


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance in kilometers between two lat/lon coordinates."""
    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@dataclass
class MigrationPoint:
    person_id: str
    event_type: str
    place_name: str
    latitude: float
    longitude: float
    year: Optional[int] = None
    jdn: Optional[int] = None


class MigrationEngine:
    def __init__(self, session: Session):
        self.session = session

    def get_person_migration_trail(self, person_id: str) -> List[MigrationPoint]:
        """Returns chronological list of migration points for a given person."""
        stmt = (
            select(EventModel)
            .where(EventModel.person_id == person_id)
            .where(EventModel.place_id.isnot(None))
            .order_by(EventModel.jdn_min.asc())
        )
        events = self.session.scalars(stmt).all()

        trail: List[MigrationPoint] = []
        for ev in events:
            if not ev.place:
                continue
            if ev.place.latitude is not None and ev.place.longitude is not None:
                year = None
                if ev.date_raw:
                    import re
                    m = re.search(r"\b(1\d{3}|20\d{2})\b", ev.date_raw)
                    if m:
                        year = int(m.group(1))

                trail.append(MigrationPoint(
                    person_id=person_id,
                    event_type=ev.event_type.value,
                    place_name=ev.place.name,
                    latitude=ev.place.latitude,
                    longitude=ev.place.longitude,
                    year=year,
                    jdn=ev.jdn_min
                ))

        return trail
