"""Pont pytest (facultatif) pour test_voix.py et test_autonomie.py.

Ces deux fichiers sont des scripts autonomes (ils s'exécutent dès qu'on les
lance) : pytest ne doit pas les importer. Ce fichier les lance chacun dans
un processus séparé et exige le code de sortie 0. Sans pytest, lancez-les
directement avec python3.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _run(name: str) -> None:
    r = subprocess.run([sys.executable, str(HERE / name)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]


def test_voix():
    _run("test_voix.py")


def test_autonomie():
    _run("test_autonomie.py")
