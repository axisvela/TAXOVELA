"""Regression tests for deterministic draw.io orthogonal edge routing."""

import copy
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams.generator import generate_drawio  # noqa: E402
from archharness.diagrams.labels import component_fill  # noqa: E402
from archharness.diagrams.layout import calculate_layout  # noqa: E402
from archharness.diagrams.routing import (  # noqa: E402
    GUTTER, LANE_GAP, MAX_VISIBILITY_NODES, ROUTING_POLICY, Rect, route,
    routing_context, scoped_rails,
)


class OrthogonalRoutingTests(unittest.TestCase):
    def test_routes_around_blocking_component(self):
        source = Rect(0, 0, 80, 40)
        target = Rect(300, 0, 80, 40)
        blocking = Rect(140, 0, 70, 40)

        result = route(source, target, [blocking])

        self.assertFalse(result.fallback)
        self.assertGreaterEqual(len(result.points), 2)
        self.assertIn(result.strategy, {"midpoint-x", "midpoint-y", "visibility-graph", "outer-top", "outer-bottom"})
        # A horizontal direct route would have y=20 throughout and hit blocker.
        self.assertTrue(any(y != 20 for _x, y in result.points))
        # Every explicit waypoint must remain outside the obstacle's clearance
        # rectangle; otherwise draw.io could cut through the component.
        clearance = blocking.expanded(14)
        for x, y in result.points:
            self.assertFalse(clearance.x <= x <= clearance.right and
                             clearance.y <= y <= clearance.bottom)

    def test_region_gutter_is_preferred_for_cross_boundary_route(self):
        source = Rect(0, 0, 50, 50)
        target = Rect(300, 100, 50, 50)

        result = route(source, target, [], rails_x=(100,))

        self.assertFalse(result.fallback)
        self.assertEqual(result.strategy, "region-gutter")
        self.assertEqual(result.points, ((100, 25), (100, 125)))
        self.assertEqual((result.exit_x, result.exit_y), (1.0, 0.5))
        self.assertEqual((result.entry_x, result.entry_y), (0.0, 0.5))

    def test_generator_emits_constraints_and_waypoints_for_cross_dc_edge(self):
        arch = {
            "id": "routing-demo",
            "name": "Routing Demo",
            "deployment": [
                {"id": "dc-a", "type": "private_dc", "name": "DC A",
                 "network_zones": [{"id": "app", "name": "App", "components": [
                     {"id": "api", "name": "API", "type": "BE"},
                 ]}]},
                {"id": "dc-b", "type": "private_dc", "name": "DC B",
                 "network_zones": [{"id": "db", "name": "DB", "components": [
                     {"id": "database", "name": "Database", "type": "DB"},
                 ]}]},
            ],
            "interactions": [{"from": "api", "to": "database", "protocol": "JDBC", "auth": "mTLS"}],
        }

        diagnostics = []
        root = ET.fromstring(generate_drawio(arch, diagnostics))
        edges = [cell for cell in root.iter("mxCell") if cell.get("edge") == "1"]

        self.assertEqual(len(edges), 1)
        style = edges[0].get("style", "")
        self.assertIn("exitX=", style)
        self.assertIn("entryX=", style)
        geometry = edges[0].find("mxGeometry")
        self.assertIsNotNone(geometry.find("Array[@as='points']"))
        self.assertEqual(edges[0].get("routingStrategy"), "region-gutter")
        self.assertEqual(edges[0].get("routingFallback"), "false")
        self.assertEqual(diagnostics, [{
            "source": "api", "target": "database", "lane": 0,
            "strategy": "region-gutter", "fallback": False,
            "waypoint_count": 2,
            "duration_ns": diagnostics[0]["duration_ns"],
        }])
        self.assertGreaterEqual(diagnostics[0]["duration_ns"], 0)

    def test_routing_controls_come_from_diagram_style_standard(self):
        self.assertEqual(ROUTING_POLICY, {
            "gutter": 28, "lane_gap": 14, "max_visibility_nodes": 256,
        })
        self.assertEqual((GUTTER, LANE_GAP, MAX_VISIBILITY_NODES), (28, 14, 256))

    def test_load_balancer_and_firewall_use_distinct_standard_shapes(self):
        arch = {
            "id": "shape-demo", "name": "Shape Demo",
            "deployment": [{"id": "dc", "type": "private_dc", "name": "DC",
                            "network_zones": [{"id": "app", "name": "App", "components": [
                                {"id": "load-balancer", "name": "Load Balancer", "type": "LB"},
                                {"id": "firewall", "name": "Firewall", "type": "SEC", "shape": "hexagon"},
                            ]}]}],
            "interactions": [],
        }
        xml = generate_drawio(arch)

        self.assertIn("shape=trapezoid;perimeter=trapezoidPerimeter", xml)
        self.assertIn("shape=hexagon;perimeter=hexagonPerimeter2", xml)

    def test_explicit_standard_shapes_override_component_defaults(self):
        arch = {
            "id": "catalogue-demo", "name": "Catalogue Demo",
            "deployment": [{"id": "dc", "type": "private_dc", "name": "DC",
                            "network_zones": [{"id": "app", "name": "App", "components": [
                                {"id": "agent", "name": "Agent", "type": "BE", "shape": "pentagon"},
                                {"id": "files", "name": "Files", "type": "DB", "shape": "card"},
                                {"id": "config", "name": "Config", "type": "BE", "shape": "double_ellipse"},
                                {"id": "pipeline", "name": "Pipeline", "type": "BE", "shape": "step"},
                            ]}]}],
            "interactions": [],
        }
        xml = generate_drawio(arch)

        for shape in ("shape=pentagon", "shape=card", "shape=doubleEllipse", "shape=mxgraph.flowchart.step"):
            self.assertIn(shape, xml)

    def test_standard_ownership_colours_override_lifecycle_colours(self):
        self.assertEqual(component_fill({"status": "NEW"})["fill"], "#D32F2F")
        self.assertEqual(component_fill({"status": "EXISTING"})["fill"], "#FFFFFF")
        self.assertEqual(component_fill({"status": "NEW", "owner": "biz_owned"})["fill"], "#8E24AA")
        self.assertEqual(component_fill({"status": "CHANGED", "owner": "third_party"})["fill"], "#FB8C00")

    def test_private_dc_zones_use_standard_security_palette(self):
        arch = {
            "id": "zone-colour-demo", "name": "Zone Colour Demo",
            "deployment": [{"id": "dc", "type": "private_dc", "name": "DC", "network_zones": [
                {"id": "dmz", "name": "DMZ", "type": "dmz", "components": []},
                {"id": "app", "name": "App", "type": "app_zone", "components": []},
                {"id": "data", "name": "Data", "type": "db_zone", "components": []},
            ]}], "interactions": [],
        }
        xml = generate_drawio(arch)

        for colour in ("fillColor=#FFF9C4;strokeColor=#D6B656", "fillColor=#E8F5E9;strokeColor=#82B366",
                       "fillColor=#E3F2FD;strokeColor=#6C8EBF"):
            self.assertIn(colour, xml)

    def test_generation_is_byte_deterministic(self):
        arch = {
            "id": "stable-routing-demo",
            "name": "Stable Routing Demo",
            "deployment": [{"id": "dc", "type": "private_dc", "name": "DC",
                            "network_zones": [{"id": "app", "name": "App", "components": [
                                {"id": "api", "name": "API", "type": "BE"},
                                {"id": "worker", "name": "Worker", "type": "BE"},
                            ]}]}],
            "interactions": [
                {"from": "api", "to": "worker", "protocol": "HTTPS", "auth": "mTLS"},
                {"from": "worker", "to": "api", "protocol": "HTTPS", "auth": "mTLS"},
            ],
        }

        first = generate_drawio(arch)
        second = generate_drawio(arch)

        self.assertEqual(first, second)

    def test_concurrent_generation_keeps_ids_local_to_each_diagram(self):
        arch = {
            "id": "concurrent-routing-demo",
            "name": "Concurrent Routing Demo",
            "deployment": [{"id": "dc", "type": "private_dc", "name": "DC",
                            "network_zones": [{"id": "app", "name": "App", "components": [
                                {"id": "api", "name": "API", "type": "BE"},
                                {"id": "worker", "name": "Worker", "type": "BE"},
                            ]}]}],
            "interactions": [{"from": "api", "to": "worker", "protocol": "HTTPS", "auth": "mTLS"}],
        }
        with ThreadPoolExecutor(max_workers=4) as executor:
            diagrams = list(executor.map(lambda _index: generate_drawio(copy.deepcopy(arch)), range(8)))

        self.assertEqual(len(set(diagrams)), 1)

    def test_reverse_cross_dc_edges_use_separate_gutter_lanes(self):
        arch = {
            "id": "reverse-routing-demo",
            "name": "Reverse Routing Demo",
            "deployment": [
                {"id": "dc-a", "type": "private_dc", "name": "DC A",
                 "network_zones": [{"id": "app", "name": "App", "components": [
                     {"id": "api", "name": "API", "type": "BE"},
                 ]}]},
                {"id": "dc-b", "type": "private_dc", "name": "DC B",
                 "network_zones": [{"id": "data", "name": "Data", "components": [
                     {"id": "database", "name": "Database", "type": "DB"},
                 ]}]},
            ],
            "interactions": [
                {"from": "api", "to": "database", "protocol": "JDBC", "auth": "mTLS"},
                {"from": "database", "to": "api", "protocol": "JDBC", "auth": "mTLS"},
            ],
        }

        root = ET.fromstring(generate_drawio(arch))
        edges = [cell for cell in root.iter("mxCell") if cell.get("edge") == "1"]
        gutters = []
        exit_ports = []
        for edge in edges:
            geometry = edge.find("mxGeometry")
            points = geometry.find("Array[@as='points']")
            self.assertEqual(edge.get("routingStrategy"), "region-gutter")
            self.assertIsNotNone(points)
            gutters.append(points.findall("mxPoint")[0].get("x"))
            exit_ports.append(edge.get("style", "").split("exitY=")[1].split(";")[0])

        self.assertEqual(len(edges), 2)
        self.assertNotEqual(gutters[0], gutters[1])
        self.assertNotEqual(exit_ports[0], exit_ports[1])

    def test_gutters_are_scoped_to_interaction_containers(self):
        arch = {
            "deployment": [
                {"id": "dc-a", "type": "private_dc", "name": "DC A",
                 "network_zones": [{"id": "app-a", "name": "App A", "components": [
                     {"id": "api-a", "name": "API A", "type": "BE"},
                 ]}]},
                {"id": "dc-b", "type": "private_dc", "name": "DC B",
                 "network_zones": [{"id": "app-b", "name": "App B", "components": [
                     {"id": "api-b", "name": "API B", "type": "BE"},
                 ]}]},
                {"id": "dc-c", "type": "private_dc", "name": "DC C",
                 "network_zones": [{"id": "app-c", "name": "App C", "components": [
                     {"id": "api-c", "name": "API C", "type": "BE"},
                 ]}]},
            ],
        }
        _rects, _owners, region_rails, _zone_rails = routing_context(arch, calculate_layout(arch))

        selected_x, selected_y = scoped_rails(
            ("dc-a", "app-a"), ("dc-b", "app-b"), region_rails, _zone_rails
        )

        self.assertEqual(selected_x, tuple(sorted(set(region_rails["dc-a"] + region_rails["dc-b"]))))
        self.assertEqual(selected_y, tuple(sorted(set(_zone_rails["app-a"] + _zone_rails["app-b"]))))

    def test_visibility_graph_avoids_canvas_wide_detour(self):
        source = Rect(0, 0, 80, 40)
        target = Rect(300, 0, 80, 40)
        blocking = Rect(140, 0, 70, 40)

        result = route(source, target, [blocking])

        self.assertFalse(result.fallback)
        self.assertEqual(result.strategy, "visibility-graph")
        # The visibility path follows the blocker clearance (y=-15), rather
        # than using the more distant outer fallback rail (y=-42).
        self.assertTrue(any(y == -15 for _x, y in result.points))

    def test_visibility_graph_handles_dense_obstacles(self):
        source = Rect(0, 60, 50, 40)
        target = Rect(900, 60, 50, 40)
        blockers = [Rect(100 + index * 75, 40, 45, 80) for index in range(10)]

        result = route(source, target, blockers)

        self.assertFalse(result.fallback)
        self.assertEqual(result.strategy, "visibility-graph")
        self.assertTrue(result.points)

    def test_oversized_visibility_grid_uses_outer_fallback(self):
        source = Rect(0, 60, 50, 40)
        target = Rect(4_000, 60, 50, 40)
        blockers = [Rect(100 + index * 75, -100 + index * 10, 45, 400) for index in range(40)]

        result = route(source, target, blockers)

        self.assertFalse(result.fallback)
        self.assertIn(result.strategy, {"outer-left", "outer-right", "outer-top", "outer-bottom"})


if __name__ == "__main__":
    unittest.main()
