from __future__ import annotations

import gzip
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional


SECTION_HEADERS = {
    "*SPEF",
    "*DESIGN",
    "*DATE",
    "*VENDOR",
    "*PROGRAM",
    "*VERSION",
    "*DESIGN_FLOW",
    "*DIVIDER",
    "*DELIMITER",
    "*BUS_DELIMITER",
    "*T_UNIT",
    "*C_UNIT",
    "*R_UNIT",
    "*L_UNIT",
    "*PORTS",
    "*NAME_MAP",
    "*D_NET",
    "*CONN",
    "*CAP",
    "*RES",
    "*END",
    "*Q",
    "*QUALITY",
}


@dataclass
class NetData:
    name: str
    raw_name: str
    total_c: float = 0.0
    total_r: float = 0.0
    declared_c: float = 0.0
    cap_sum: float = 0.0
    coupling_cap_sum: float = 0.0
    quality: Optional[float] = None
    cap_entries: int = 0
    res_entries: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def rc(self) -> float:
        return self.total_r * self.total_c


@dataclass
class SpefData:
    path: Path
    name_map: Dict[str, str]
    nets: Dict[str, NetData]


def open_spef(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def resolve_name(token: str, name_map: Dict[str, str]) -> str:
    return name_map.get(token, token)


def _strip_spef_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def _iter_lines(path: Path) -> Iterable[str]:
    with open_spef(path) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line:
                yield line


def _parse_quality(tokens: list[str]) -> Optional[float]:
    for token in tokens:
        try:
            return float(token)
        except ValueError:
            continue
    return None


def parse_spef(path: str | Path) -> SpefData:
    spef_path = Path(path)
    name_map: Dict[str, str] = {}
    nets: Dict[str, NetData] = {}

    in_name_map = False
    current_net: Optional[NetData] = None
    current_subsection: Optional[str] = None

    for line in _iter_lines(spef_path):
        if line.startswith("//"):
            continue

        tokens = line.split()
        if not tokens:
            continue

        keyword = tokens[0]

        if keyword == "*NAME_MAP":
            in_name_map = True
            current_subsection = None
            current_net = None
            continue

        if in_name_map and keyword not in SECTION_HEADERS and len(tokens) >= 2:
            mapped_name = line[len(tokens[0]) :].strip()
            name_map[tokens[0]] = _strip_spef_quotes(mapped_name)
            continue

        if keyword in SECTION_HEADERS and keyword != "*NAME_MAP":
            in_name_map = False

        if keyword == "*D_NET":
            if len(tokens) < 2:
                current_net = None
                current_subsection = None
                continue
            raw_name = tokens[1]
            total_c = 0.0
            if len(tokens) >= 3:
                try:
                    total_c = float(tokens[2])
                except ValueError:
                    total_c = 0.0
            current_net = NetData(
                name=resolve_name(raw_name, name_map),
                raw_name=raw_name,
                total_c=total_c,
                declared_c=total_c,
            )
            if len(tokens) > 3:
                current_net.quality = _parse_quality(tokens[3:])
            nets[current_net.name] = current_net
            current_subsection = None
            continue

        if current_net is None:
            continue

        if keyword in {"*CONN", "*CAP", "*RES"}:
            current_subsection = keyword
            continue

        if keyword in {"*Q", "*QUALITY"}:
            current_net.quality = _parse_quality(tokens[1:])
            continue

        if keyword == "*END":
            current_net = None
            current_subsection = None
            continue

        if current_subsection == "*CAP":
            if len(tokens) < 3:
                continue
            value_token = tokens[-1]
            try:
                value = float(value_token)
            except ValueError:
                continue
            current_net.cap_entries += 1
            if len(tokens) == 3:
                current_net.cap_sum += value
            elif len(tokens) >= 4:
                current_net.coupling_cap_sum += value
            else:
                continue
            current_net.metadata["cap_sum"] = str(current_net.cap_sum)
            current_net.metadata["coupling_cap_sum"] = str(current_net.coupling_cap_sum)
            continue

        if current_subsection == "*RES":
            if len(tokens) < 4:
                continue
            value_token = tokens[-1]
            try:
                value = float(value_token)
            except ValueError:
                continue
            current_net.res_entries += 1
            current_net.total_r += value
            continue

    return SpefData(path=spef_path, name_map=name_map, nets=nets)
