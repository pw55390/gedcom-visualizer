"""
Unit tests for KinshipGraphEngine, AncestorsLayout, and DiagramExporter.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from src.database.engine import DatabaseEngine
from src.database.repositories.person_repository import PersonRepository
from src.database.repositories.family_repository import FamilyRepository
from src.core.enums import Sex, UnionType
from src.visualization.graph_engine import KinshipGraphEngine
from src.visualization.layouts.ancestors_layout import AncestorsLayout
from src.visualization.exporters import DiagramExporter


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_graph_topology_engine(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    family_repo = FamilyRepository(session)

    # Build 3-generation family
    g_father = person_repo.create_person(given_names="Dziadek", surname="Kowalski", sex=Sex.MALE)
    g_mother = person_repo.create_person(given_names="Babcia", surname="Kowalska", sex=Sex.FEMALE)
    father = person_repo.create_person(given_names="Ojciec", surname="Kowalski", sex=Sex.MALE)
    child = person_repo.create_person(given_names="Dziecko", surname="Kowalski", sex=Sex.MALE)

    session.commit()

    f1 = family_repo.create_family(husband_id=g_father.id, wife_id=g_mother.id)
    family_repo.add_child(f1.id, father.id)

    f2 = family_repo.create_family(husband_id=father.id)
    family_repo.add_child(f2.id, child.id)
    session.commit()

    # Test KinshipGraphEngine
    graph_engine = KinshipGraphEngine(session)
    ancestors, edges = graph_engine.get_ancestors_subgraph(child.id, max_generations=5)

    assert child.id in ancestors
    assert father.id in ancestors
    assert g_father.id in ancestors
    assert len(ancestors) == 4

    # Path finding
    path = graph_engine.find_shortest_kinship_path(child.id, g_father.id)
    assert path is not None
    assert len(path) == 3  # child -> father -> g_father

    session.close()


def test_ancestors_layout_calculation(db_engine):
    session = db_engine.get_session()
    person_repo = PersonRepository(session)
    family_repo = FamilyRepository(session)

    p1 = person_repo.create_person(given_names="Ojciec", surname="Kowalski", sex=Sex.MALE)
    p2 = person_repo.create_person(given_names="Dziecko", surname="Kowalski", sex=Sex.MALE)
    session.commit()

    f = family_repo.create_family(husband_id=p1.id)
    family_repo.add_child(f.id, p2.id)
    session.commit()

    graph_engine = KinshipGraphEngine(session)
    layout = AncestorsLayout()
    positions, edges = layout.calculate_layout(p2.id, graph_engine)

    assert p2.id in positions
    assert p1.id in positions
    assert positions[p2.id][1] == 0.0  # Root at Y=0
    assert positions[p1.id][1] < 0.0   # Parent above root (Y < 0)

    # Test Spouse layout rendering at Level 0
    wife = person_repo.create_person(given_names="Matka", surname="Kowalska", sex=Sex.FEMALE)
    session.commit()
    family_repo.create_family(husband_id=p1.id, wife_id=wife.id)
    session.commit()

    graph_engine.rebuild_graph()
    positions_p1, edges_p1 = layout.calculate_layout(p1.id, graph_engine, max_descendants=1)
    assert p1.id in positions_p1
    assert wife.id in positions_p1
    assert p2.id in positions_p1
    assert positions_p1[p1.id][1] == 0.0
    assert positions_p1[wife.id][1] == 0.0
    assert positions_p1[p2.id][1] > 0.0   # Child below parents (Y > 0)

    session.close()


def test_diagram_exporter(qapp, tmp_path):
    scene = QGraphicsScene()
    scene.addRect(0, 0, 100, 100)

    png_path = str(tmp_path / "test_diagram.png")
    svg_path = str(tmp_path / "test_diagram.svg")

    DiagramExporter.export_to_png(scene, png_path)
    DiagramExporter.export_to_svg(scene, svg_path)

    assert os.path.exists(png_path)
    assert os.path.exists(svg_path)
    assert os.path.getsize(png_path) > 0
    assert os.path.getsize(svg_path) > 0
