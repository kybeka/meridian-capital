"""Compatibility entry point for the canonical Bloomberg optimizer."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('revalidate_bloomberg.py')),run_name='__main__')
