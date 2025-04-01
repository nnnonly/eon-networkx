from typing import List
from src.ProtectingLightPath import ProtectingLightPath

class PCycle:
    def __init__(self, cycle_links, protected_lightpaths=List[ProtectingLightPath], be_protection = List[ProtectingLightPath], reserved_slots=0):
        """
        Initialize P-cycle
        :param cycle_links: List of links in P-cycle [(src1, dst1), (src2, dst2), ...]
        :param protected_lightpaths: List of protected lightpaths
        :param reserved_slots: Set of reserved spectrum slots
        """
        self.cycle_links = cycle_links
        self.protected_lightpaths = protected_lightpaths if protected_lightpaths else []
        self.be_protection = be_protection if be_protection else []
        self.reserved_slots = reserved_slots

    def add_protected_lightpath(self, lightpath):
        if lightpath not in self.protected_lightpaths:
            self.protected_lightpaths.append(lightpath)

    def remove_protected_lightpath(self, lightpath):
        if lightpath in self.protected_lightpaths:
            self.protected_lightpaths.remove(lightpath)

    def p_cycle_contains_flow(self, src, dst):
        """
        Check if the P-cycle contains the flow
        :param p_cycle: List of links in P-cycle
        :param src: Source node
        :param dst: Destination node
        :return: True if the P-cycle contains the flow, False otherwise
        """
        nodes_in_p_cycle = set()
        for u, v in self.cycle_links:
            nodes_in_p_cycle.add(u)
            nodes_in_p_cycle.add(v)
        return src in nodes_in_p_cycle and dst in nodes_in_p_cycle


    def has_sufficient_slots(self, required_slots):
        return len(self.reserved_slots) >= required_slots

    def can_protect(self, primary_path):
        for link in primary_path:
            if link in self.cycle_links:  # On-cycle protection
                return True
        return False

    def get_edges(path):
        # Convert path into list of edges
        return set((path[i], path[i + 1]) for i in range(len(path) - 1))

    def get_all_lp(self, lps: List[ProtectingLightPath]) -> List[List[int]]:
        """get all lightpaths that are protected by the P-cycle"""
        paths = []
        for lp in lps:
            paths.append(lp.get_links())
        return paths

    def add_links_disjoint(self, new_lp: List[int]):
        """add links p-cycle can protect"""
        if self.protected_lightpaths:
            lp_protected = self.get_all_lp(self.protected_lightpaths)
            new_lp_protected = get_eges(new_lp)

            for idx, path in enumerate(lp_protected):
                edges = get_edges(path)

                if not new_lp_protected.isdisjoint(edges):
                    return False


            return True


    def __str__(self):
        return f"P-cycle: {self.cycle_links}, Protected Paths: {len(self.protected_lightpaths)}, Reserved Slots: {self.reserved_slots}"
