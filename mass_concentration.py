#!/usr/bin/env python

from __future__ import division

import sys

import numpy as np
from scipy import optimize as opt

from astropy import units as u
from astropy import cosmology

def _diff_c(c1, c0, delta_ratio):
    return _delta_fac(c0) / _delta_fac(c1) - delta_ratio * (c0 / c1)**3

def _findc(c0, overdensity_in, overdensity_out):
    delta_ratio = overdensity_out / overdensity_in    
    return opt.brentq(_diff_c, .01, 1000, args=(c0, delta_ratio))

def _delta_fac(c):
    return np.log(1 + c) - c / (1 + c)

def _find_m200(m200, *args):
    func = args[0]
    overdensity_in = args[1]
    overdensity_out = args[2]
    m_in = args[3]
    my_args = args[4:]
    c0 = func(m200, *my_args)
    c1 = _findc(c0, overdensity_in, overdensity_out)
    return m200 / m_in.value - _delta_fac(c0) / _delta_fac(c1)


def mdelta_to_mdelta(m, func, overdensity_in, overdensity_out, args=()):
    """
    Convert the a mass given in a variable overdensity with respect to
    the critical density to the mass in another overdensity wrt the
    critical density following a fixed mass concentration relation.

    Parameters:
    ===========
    m: float or astropy.Quantity
        mass of halo
    func: callable func(m200c, *args)
        Mass-concentration scaling relation
    overdensity_in: float
        Overdensity in units of rho_crit at which halo mass is set
    overdensity_out: float
        Overdensity in units of rho_crit at which halo mass is desired
    args: tuple, optional
        Extra arguments passed to func, i.e., ``f(x, *args)``.

    Returns:
    ========
    mdelta: astropy.Quantity
        mass of halo at Delta times critical overdensity

    Notes:
    ====== 
    Halo masses must be given in units expected by the M-c relation.
    """
    m_in = u.Quantity(m, u.solMass)
    if overdensity_in == overdensity_out:
        # brentq will fail for identical
        return m_in
    delta_ratio = overdensity_in / overdensity_out
    m_min = u.Quantity(1e5, u.solMass)
    m_max = u.Quantity(1e25, u.solMass)
    mdelta = opt.brentq(_find_m200, m_min.value, m_max.value,
                       args=(func, overdensity_in, overdensity_out, m_in) \
                        + args)
    return u.Quantity(mdelta, u.solMass)


def mdelta_to_m200(m, func, overdensity, args=()):
    """
    Convenience function for mdelta_to_mdelta with output overdensity 200.

    Parameters:
    ===========
    m: float or astropy.Quantity
        mass of halo
    func: callable func(m200c, *args)
        Mass-concentration scaling relation
    overdensity: float
        Overdensity in units of rho_crit at which halo mass is set
    args: tuple, optional
        Extra arguments passed to func, i.e., ``f(x, *args)``.

    Returns:
    ========
    m200: astropy.Quantity
        mass of halo at 200 times critical overdensity

    Notes:
    ======
    Halo masses must be given in units expected by the M-c relation.
    """
    return mdelta_to_mdelta(m, func, overdensity, 200, args)


def dolag_concentration(m200, z, cosmo):
    """
    Compute the concentration of the Dolag et al. (2004)
    mass concentration relation for a standard LCDM universe.

    Parameters:
    ===========

    m200: astropy.Quantity
        Mass of halo at 200rho_crit
    z: float
        Halo redshift
    cosmo: astropy.cosmology

    Returns:
    ========
    conc: float
        Halo concentration

    Notes:
    ======
    Halo masses must be given in physical units with factors of h
    divided out.
    """
    m200 = np.asanyarray(m200)
    z = np.asanyarray(z)
    m200 = u.Quantity(m200 * cosmo.h, u.solMass).value
    conc = 9.59 / (1 + z) * (m200 / 1e14)**-0.102
    return conc

  
def duffy_concentration(m200, z, cosmo):
    """
    Compute the concentration of the Duffy et al. (2008)
    mass concentration relation for 200 rho_crit.

    Parameters:
    ===========

    m200: float, array_like or astropy.Quantity
        Mass of halo at 200rho_crit, [Msun] if float
    z: float or array_like
        Halo redshift
    cosmo: astropy.cosmology

    Returns:
    ========
    conc: float or array
        Halo concentration

    Notes:
    ======
    Halo masses must be given in physical units with factors of h
    divided out.
    """

    m200 = np.asanyarray(m200)
    z = np.asanyarray(z)
    m200 = u.Quantity(m200 * cosmo.h, u.solMass)
    a = 5.71
    b = -0.084
    c = -0.47
    m_pivot = u.Quantity(2e12, u.solMass)
    conc = a * (m200 / m_pivot)**b * (1 + z)**c
    return conc.value

