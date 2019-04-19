#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position

"""
Convert a CLSim 5D and/or Cherenkov 5D table -- with dimensions
(r, costheta, t, costhetadir, deltaphidir) -- into time-independent 4D table(s)
with dimensions (r, costheta, costhetadir, deltaphidir)..
"""

from __future__ import absolute_import, division, print_function

__all__ = [
    'generate_time_indep_tables',
    'parse_args'
]

from argparse import ArgumentParser
from os.path import abspath, basename, dirname, isdir, isfile, join
import sys
import time

import numpy as np
from six import string_types

if __name__ == '__main__' and __package__ is None:
    RETRO_DIR = dirname(dirname(dirname(abspath(__file__))))
    if RETRO_DIR not in sys.path:
        sys.path.append(RETRO_DIR)
import retro
from retro.tables.clsim_tables import load_clsim_table_minimal
from retro.tables.ckv_tables import load_ckv_table
from retro.utils.misc import expand, mkdir


def generate_time_indep_tables(
        table,
        kind,
        outdir=None,
        overwrite=False
    ):
    """Generate and save to disk time independent table(s) from the original
    CLSim table and/or a Cherenkov table.

    Parameters
    ----------
    table : string
    kind : string in {"ckv", "clsim"} or iterable of one or more
    outdir : string, optional
    overwrite : bool, optional

    Returns
    -------
    t_indep_table : numpy.ndarray of size (n_r, n_costheta, n_costhetadir, n_deltaphidir)

    """
    if isinstance(kind, string_types):
        kind = [kind]
    kinds = [k.strip().lower() for k in kind]

    clsim_table_path = None
    ckv_table_path = None

    table = expand(table)
    if outdir is None:
        if isdir(table):
            outdir = table
        elif table.endswith('.npy'):
            outdir = dirname(table)
        elif table.endswith('.fits'):
            outdir = table.rstrip('.fits')

    if isfile(table):
        table_basename = basename(table)
        if table_basename == 'table.npy' or table_basename.endswith('.fits'):
            clsim_table_path = table
        elif table_basename == 'ckv_table.npy':
            ckv_table_path = table

    elif isdir(table):
        if 'clsim' in kinds and isfile(join(table, 'table.npy')):
            clsim_table_path = table

        if 'ckv' in kinds and isfile(join(table, 'ckv_table.npy')):
            ckv_table_path = table

    t_indep_table_exists = False
    t_indep_table_fpath = join(outdir, 't_indep_table.npy')
    if 'clsim' in kinds and isfile(t_indep_table_fpath):
        t_indep_table_exists = True
        if overwrite:
            print('WARNING: t_indep_table already exists, overwriting: "{}"'
                  .format(t_indep_table_fpath))
        else:
            print('t_indep_table already exists, not overwriting: "{}"'
                  .format(t_indep_table_fpath))

    t_indep_ckv_table_exists = False
    t_indep_ckv_table_fpath = join(outdir, 't_indep_ckv_table.npy')
    if 'ckv' in kinds and isfile(t_indep_ckv_table_fpath):
        t_indep_ckv_table_exists = True
        if overwrite:
            print('WARNING: t_indep_ckv_table already exists, overwriting: "{}"'
                  .format(t_indep_ckv_table_fpath))
        else:
            print('t_indep_ckv_table already exists, not overwriting: "{}"'
                  .format(t_indep_ckv_table_fpath))

    if 'clsim' in kinds and (overwrite or not t_indep_table_exists):
        if clsim_table_path is None:
            raise ValueError(
                'Told to generate t-indep table from CLSim table but CLSim'
                ' table does not exist.'
            )
        print('generating t_indep_table at "{}"'.format(clsim_table_path))
        mkdir(outdir)
        t0 = time.time()

        clsim_table = load_clsim_table_minimal(clsim_table_path, mmap=True)

        t1 = time.time()
        if retro.DEBUG:
            print('loaded clsim table in {:.3f} s'.format(t1 - t0))

        t_indep_table = clsim_table['table'][1:-1, 1:-1, 1:-1, 1:-1, 1:-1].sum(axis=2)

        t2 = time.time()
        if retro.DEBUG:
            print('summed over t-axis in {:.3f} s'.format(t2 - t1))

        np.save(t_indep_table_fpath, t_indep_table)

        t3 = time.time()
        if retro.DEBUG:
            print('saved t_indep_table.npy to disk in {:.3f} s'.format(t3 - t2))

        del clsim_table, t_indep_table

    if 'ckv' in kinds and (overwrite or not t_indep_ckv_table_exists):
        if ckv_table_path is None:
            raise ValueError(
                'Told to generate t-indep table from ckv table but ckv'
                ' table does not exist.'
            )
        print('generating t_indep_ckv_table at "{}"'.format(ckv_table_path))
        mkdir(outdir)
        t0 = time.time()

        ckv_table = load_ckv_table(ckv_table_path, mmap=True)

        t1 = time.time()
        if retro.DEBUG:
            print('loaded ckv table in {:.3f} s'.format(t1 - t0))

        t_indep_ckv_table = ckv_table['ckv_table'].sum(axis=2)

        t2 = time.time()
        if retro.DEBUG:
            print('summed over t-axis in {:.3f} s'.format(t2 - t1))

        np.save(t_indep_ckv_table_fpath, t_indep_ckv_table)

        t3 = time.time()
        if retro.DEBUG:
            print('saved t_indep_table.npy to disk in {:.3f} s'.format(t3 - t2))

        del ckv_table, t_indep_ckv_table


def parse_args(description=__doc__):
    """Parse command line arguments"""
    parser = ArgumentParser(description=description)
    parser.add_argument(
        'table',
        help='''5D table to make 4D'''
    )
    parser.add_argument(
        '--outdir', default=None,
        help='''If --outdir is not specified, the output is placed in the
        .npy-file directory corresponding to the input.'''
    )
    parser.add_argument(
        '--kind', required=True, choices=['clsim', 'ckv'], action='append',
        help='''Process the specified kind(s) of table(s) within that dir.
        Repeat --kind for multiple.'''
    )
    parser.add_argument(
        '--overwrite', action='store_true',
        help='''Overwrite any existing time-independent tables.'''
    )
    parser.add_argument(
        '-v', action='store_true'
    )
    kwargs = vars(parser.parse_args())
    verbosity = kwargs.pop('v')
    if verbosity:
        retro.DEBUG = 1
    return kwargs


if __name__ == '__main__':
    generate_time_indep_tables(**parse_args())
