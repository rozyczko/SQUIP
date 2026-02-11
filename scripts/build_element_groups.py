#!/usr/bin/env python3
"""Build element-based atom index groups using MDAnalysis."""

import MDAnalysis as mda

WATER_RESNAMES = {"SOL", "WAT", "HOH", "TIP3", "TIP3P", "TIP4", "TIP4P", "T4E"}


def guess_element(atom):
    if atom.element:
        return atom.element.capitalize()
    return atom.name[0].upper()


def build_element_groups(universe, selection=None):
    if selection:
        atoms = universe.select_atoms(selection)
    else:
        atoms = universe.atoms

    groups = {}
    for atom in atoms:
        elem = guess_element(atom)
        groups.setdefault(elem, []).append(atom.index)  # 0-based
    return groups


def build_solute_h_groups(universe):
    solute_sel = "not resname " + " ".join(sorted(WATER_RESNAMES))
    solute_h_sel = f"({solute_sel}) and name H*"
    return build_element_groups(universe, selection=solute_h_sel)
