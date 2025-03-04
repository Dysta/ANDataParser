from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

from .depute import Depute


@dataclass(frozen=True, eq=False)
class Amendement:
    id: int
    name: str
    url: str
    date: str
    status: str
    proposed_by: Union[List[Depute], str]
    summary: Optional[str]

    # analyse: ScrutinAnalyse
