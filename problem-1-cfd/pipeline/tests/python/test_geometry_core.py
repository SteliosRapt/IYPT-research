from __future__ import annotations

from services.geometry.core import (
    build_fixed_geometry_descriptors,
    create_geometry_snapshot,
)


def test_default_geometry_matches_expected_values() -> None:
    snapshot = create_geometry_snapshot()
    derived = snapshot["derived"]

    assert derived["h2"] == 0.285
    assert derived["h4"] == 0.335
    assert derived["X2"] == 0.173132896932
    assert derived["X5"] == 0.543444296177
    assert derived["H0"] == 0.228
    assert all(constraint["ok"] for constraint in snapshot["constraints"])


def test_holder_layout_and_structure_extent() -> None:
    snapshot = create_geometry_snapshot()
    parameters = snapshot["parameters"]
    derived = snapshot["derived"]
    descriptors = build_fixed_geometry_descriptors(parameters, derived)

    holder_names = [descriptor["name"] for descriptor in descriptors["holders"]]
    assert holder_names == ["W1Holder", "P3Holder", "W2Holder", "P4Holder"]

    max_x = max(
        descriptor["center"][0] + descriptor["size"][0] / 2
        for descriptor in descriptors["columns"]
        if descriptor["type"] == "box"
    )
    assert round(max_x, 12) == derived["X5"]

    assert derived["holderBases"] == [
        {"name": "W1", "x": derived["S1"], "y": 0.0},
        {"name": "P3", "x": derived["X3"], "y": 0.0},
        {"name": "W2", "x": derived["S2"], "y": 0.0},
        {"name": "P4", "x": derived["X4"], "y": parameters["h0"]},
    ]
