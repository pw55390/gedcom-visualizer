"""
Demographic & Statistical Analysis Engine powered by Pandas and NumPy.
Executes high-speed aggregations on large genealogical datasets (100k+ records).
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.core.enums import EventType
from src.database.schema import PersonModel, PersonNameModel, EventModel, PlaceModel


class DemographicStatsEngine:
    def __init__(self, session: Session):
        self.session = session

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates high-level dataset summary metrics."""
        persons = self.session.scalars(select(PersonModel)).all()
        if not persons:
            return {"total_persons": 0, "male_count": 0, "female_count": 0, "avg_lifespan": 0.0}

        df_persons = pd.DataFrame([
            {"id": p.id, "sex": p.sex.value} for p in persons
        ])

        total = len(df_persons)
        males = len(df_persons[df_persons["sex"] == "M"])
        females = len(df_persons[df_persons["sex"] == "F"])

        lifespans = self._calculate_all_lifespans()
        avg_lifespan = float(np.mean(lifespans)) if lifespans else 0.0

        return {
            "total_persons": total,
            "male_count": males,
            "female_count": females,
            "sex_ratio_male_pct": round((males / total * 100), 1) if total > 0 else 0.0,
            "avg_lifespan": round(avg_lifespan, 1)
        }

    def get_top_surnames(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top N surnames by frequency using Pandas value_counts."""
        names = self.session.scalars(select(PersonNameModel.surname).where(PersonNameModel.surname.isnot(None))).all()
        if not names:
            return []

        df_names = pd.Series(names)
        counts = df_names.value_counts().head(limit)

        return [{"surname": name, "count": int(cnt)} for name, cnt in counts.items()]

    def _calculate_all_lifespans(self) -> List[float]:
        """Extracts lifespan in years for all persons with valid birth and death JDNs."""
        events = self.session.scalars(
            select(EventModel).where(EventModel.event_type.in_([EventType.BIRTH, EventType.DEATH]))
        ).all()

        births: Dict[str, int] = {}
        deaths: Dict[str, int] = {}

        for ev in events:
            if not ev.person_id or not ev.jdn_min:
                continue
            if ev.event_type == EventType.BIRTH:
                births[ev.person_id] = ev.jdn_min
            elif ev.event_type == EventType.DEATH:
                deaths[ev.person_id] = ev.jdn_min

        lifespans = []
        for pid, b_jdn in births.items():
            if pid in deaths:
                d_jdn = deaths[pid]
                if d_jdn >= b_jdn:
                    years = (d_jdn - b_jdn) / 365.25
                    if years <= 120:
                        lifespans.append(years)

        return lifespans
