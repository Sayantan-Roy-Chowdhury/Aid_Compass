from pathlib import Path


if __name__ == "__main__":
    graph = Path(__file__).resolve().parents[1] / "docs" / "graph.mmd"
    print(graph.read_text(encoding="utf-8"))
