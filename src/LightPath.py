from typing import List
from src.Slot import Slot


class LightPath:
    def __init__(self, id: float, src: int, dst: int, links: List[int], slot_list: List[Slot], modulation_level: int):
        if id < 0 or src < 0 or dst < 0 or len(links) < 1:
            raise ValueError("IllegalArgumentException")
        else:
            self.id = id
            self.src = src
            self.dst = dst
            self.links = links
            self.slot_list = slot_list
            self.modulation_level = modulation_level

    def get_modulation_level(self) -> int:
        return self.modulation_level

    def set_modulation_level(self, modulation_level: int) -> None:
        self.modulation_level = modulation_level

    def get_id(self) -> float:
        return self.id

    def get_source(self) -> int:
        return self.src

    def get_destination(self) -> int:
        return self.dst

    def get_links(self) -> List[int]:
        return self.links

    def get_link(self, i: int) -> int:
        return self.links[i]

    def get_slot_list(self) -> List[Slot]:
        return self.slot_list

    def set_channel(self, slot_list: List[Slot]) -> None:
        self.slot_list = slot_list

    def get_hops(self) -> int:
        return len(self.links)

    def __str__(self) -> str:
        light_path = f"id:{self.id}, src: {self.src}, dst:{self.dst}, links: "
        for i in range(0, len(self.links), 1):
            light_path += f"{self.links[i]}-"
        return light_path

    def to_trace(self) -> str:
        light_path = f"{self.id} {self.src} {self.dst} "
        for i in range(0, len(self.links), 1):
            light_path += f"{self.links[i]}-"
        return light_path
