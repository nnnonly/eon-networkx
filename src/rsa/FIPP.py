import xml.etree.ElementTree as ET
from typing import List, Dict
import math
import networkx as nx
from itertools import islice

from src.rsa.RSA import RSA
from src.util.ConnectedComponent import ConnectedComponent
from src.PhysicalTopology import PhysicalTopology
from src.VirtualTopology import VirtualTopology
from src.ControlPlaneForRSA import ControlPlaneForRSA
from src.TrafficGenerator import TrafficGenerator
from src.Flow import Flow
from src.Slot import Slot
from src.PCycle import PCycle


class FIPP(RSA):
    def __init__(self):
        self.pt = None
        self.vt = None
        self.cp = None
        self.graph = None

    def simulation_interface(self, xml: ET.Element, pt: PhysicalTopology, vt: VirtualTopology, cp: ControlPlaneForRSA,
                             traffic: TrafficGenerator):
        self.pt = pt
        self.vt = vt
        self.cp = cp
        self.graph = pt.get_weighted_graph()

    def find_working_path(self, flow: Flow, demand_in_slots: int):
        """
        Find a working path for the flow
        :param flow: Flow object
        :return: working path
        """
        k_paths = list(islice(nx.shortest_simple_paths(self.graph, flow.get_source(), flow.get_destination(), weight="weight"), 5))

        spectrum = [[True for _ in range(self.pt.get_num_slots())] for _ in range(self.pt.get_cores())]
        sharing_spectrum = [[True for _ in range(self.pt.get_num_slots())] for _ in range(self.pt.get_cores())]

        primary_path = None
        regions = {}
        for k in range(0, len(k_paths), 1):
            for i in range(0, len(k_paths[k]) - 1, 1):
                spectrum = self.image_and(self.pt.get_spectrum(k_paths[k][i], k_paths[k][i + 1]),
                                          spectrum, spectrum)

            cc = ConnectedComponent()
            list_of_regions = cc.list_of_regions(spectrum)

            if list_of_regions == {}:
                continue
            fitted_slot_list = self.can_fit_connection(list_of_regions, demand_in_slots)
            if list_of_regions and fitted_slot_list:
                primary_path = k_paths[k]
                for s in fitted_slot_list:
                    spectrum[s.core][s.slot] = False
                break
        return primary_path, spectrum

    def flow_arrival(self, flow: Flow) -> None:

        demand_in_slots = math.ceil(flow.get_rate() / self.pt.get_slot_capacity())

        # find working path
        primary_path, spectrum = self.find_working_path(flow, demand_in_slots)
        if not primary_path:
            self.cp.block_flow(flow.get_id())
            return

        # find protecting path
        links = [0 for _ in range(len(primary_path) - 1)]
        for j in range(0, len(primary_path) - 1, 1):
            links[j] = self.pt.get_link_id(primary_path[j], primary_path[j + 1])

        p_cycles = self.vt.get_p_cycles()
        p_cycles_can_protect = []
        if primary_path:
            for p_cycle in p_cycles:
                if p_cycle.p_cycle_contains_flow(primary_path[0], primary_path[-1]):
                    if p_cycle.can_add_links_disjoint(links):
                        if p_cycle.has_sufficient_slots(demand_in_slots):
                            p_cycles_can_protect.append(p_cycle)
        if p_cycles_can_protect:
            p_cycles_can_protect[0].add_protected_lightpath()

        else:
            # remove links on path s1 and remove links that connect with the nodes on path s1
            g_backup = self.remove_edges(primary_path)
            if nx.has_path(g_backup, flow.get_source(), flow.get_destination()):
                k_paths_protection = list(islice(nx.shortest_simple_paths(g_backup, flow.get_source(), flow.get_destination(), weight="weight"), 5))
                if k_paths_protection:
                    for i in range(len(k_paths_protection)):
                        if self.create_p_cycle_from_paths(primary_path, k_paths_protection[i], demand_in_slots, spectrum):
                            if self.fit_connection(regions, demand_in_slots, links, flow):
                                return
                # elif self.vt.get_p_cycles():
                #     if self.vt.check_all_p_cycles_protection(primary_path[0], primary_path[-1], demand_in_slots) is not None:
                #         if self.fit_connection(regions, demand_in_slots, links, flow):
                #             return

        self.cp.block_flow(flow.get_id())
        return

    def can_fit_connection(self, list_of_regions: Dict[int, List[Slot]], demand_in_slots: int) -> List[Slot]:
        """Check if the connection can be fit into the network"""
        fitted_slot_list = []
        for key, region in list_of_regions.items():
            if len(region) >= demand_in_slots:
                for i in range(demand_in_slots):
                    fitted_slot_list.append(region[i])
        return fitted_slot_list

    def fit_connection(self, list_of_regions: Dict[int, List[Slot]], demand_in_slots: int, links: List[int],
                       flow: Flow) -> bool:
        fitted_slot_list = []
        for key, region in list_of_regions.items():
            if len(region) >= demand_in_slots:
                for i in range(demand_in_slots):
                    fitted_slot_list.append(region[i])
                if self.establish_connection(links, fitted_slot_list, 0, flow):
                    return True
        return False

    def establish_connection(self, links: List[int], slot_list: List[Slot], modulation: int, flow: Flow):
        id = self.vt.create_light_path(links, slot_list, 0)
        if id >= 0:
            lps = self.vt.get_light_path(id)
            flow.set_links(links)
            flow.set_slot_list(slot_list)
            self.cp.accept_flow(flow.get_id(), lps)
            return True
        else:
            return False

    def image_and(self, image1: List[List[bool]], image2: List[List[bool]], res: List[List[bool]]) -> List[List[bool]]:
        for i in range(len(res)):
            for j in range(len(res[0])):
                res[i][j] = image1[i][j] and image2[i][j]
        return res

    def flow_departure(self, flow):
        pass

    def create_p_cycle_from_paths(self, primary_path: List[int], backup_path: List[int], demand_in_slots: int, sharing_spectrum: List[List[bool]]) -> List[tuple]:
        """
        Create a p-cycle from primary and backup paths
        :param primary_path: Primary path
        :param backup_path: Backup path
        :param demand_in_slots: Demand in slots
        :return: List of edges of the p-cycle if it is possible to create, None otherwise
        """

        p_cycle_edges = set(zip(primary_path, primary_path[1:])) | set(zip(backup_path, backup_path[1:]))

        for i in range(0, len(primary_path) - 1, 1):
            sharing_spectrum = self.image_and(self.pt.get_sharing_spectrum(primary_path[i], primary_path[i + 1]),
                                                sharing_spectrum, sharing_spectrum)

        for i in range(0, len(backup_path) - 1, 1):
            sharing_spectrum = self.image_and(self.pt.get_sharing_spectrum(backup_path[i], backup_path[i + 1]),
                                                sharing_spectrum, sharing_spectrum)
        cc = ConnectedComponent()
        list_of_regions = cc.list_of_regions(sharing_spectrum)
        fitted_slot_list = []

        for key, region in list_of_regions.items():
            if len(region) >= demand_in_slots:
                for i in range(demand_in_slots):
                    fitted_slot_list.append(region[i])
                    new_p_cycle = PCycle(list(p_cycle_edges), reserved_slots=demand_in_slots)
                    self.vt.add_p_cycles(new_p_cycle)
                    for src, dst in p_cycle_edges:
                        self.pt.reserve_sharing_lots(src, dst, fitted_slot_list)
                    return True
        return False

    def remove_edges(self, path):
        G_modified = self.pt.get_graph().copy()
        sp1_edges = [(sp1[i], sp1[i + 1]) for i in range(len(sp1) - 1)]
        G_modified.remove_edges_from(sp1_edges)

        # Step 4: Remove links connecting to nodes on sp1 from the network
        nodes_on_sp1 = set(sp1)
        remove_edges = [(u, v) for u, v in G_modified.edges if u in nodes_on_sp1 or v in nodes_on_sp1]
        G_modified.remove_edges_from(remove_edges)
        return G_modified


