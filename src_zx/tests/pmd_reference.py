"""Referenční CPU pro PMD program s RAM i pod adresou $4000."""
from pathlib import Path
import types
from skoolkit import simulator


def ram_sim(memory, **kwargs):
    # Úprava platí pouze pro nezávislou PMD referenci uvnitř testu.
    # Spectrum se vykonává neupraveným simulátorem se skutečnou ROM.
    mod = types.ModuleType('pmd_ram_simulator')
    source = Path(simulator.__file__).read_text()
    assert '> 0x3FFF' in source
    exec(source.replace('> 0x3FFF', '>= 0'), mod.__dict__)
    return mod.Simulator(memory, **kwargs)
