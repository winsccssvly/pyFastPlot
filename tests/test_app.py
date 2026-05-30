from pathlib import Path

from pyfastplot.app import resource_path


def test_resource_path_resolves_from_project_root():
    path = resource_path(Path("assets") / "pyfastplot_icon.png")

    assert path.name == "pyfastplot_icon.png"
    assert path.parent.name == "assets"
    assert path.exists()
