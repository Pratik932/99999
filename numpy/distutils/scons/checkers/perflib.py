#! /usr/bin/env python
# Last Change: Wed Oct 31 06:00 PM 2007 J

# This module defines checkers for performances libs providing standard API,
# such as MKL (Intel), ATLAS, Sunperf (solaris and linux), Accelerate (Mac OS
# X), etc... Those checkers merely only check whether the library is found
# using a library specific check if possible, or other heuristics.
# Generally, you don't use those directly: they are used in 'meta' checkers,
# such as BLAS, CBLAS, LAPACK checkers.
import re

from numpy.distutils.scons.libinfo import get_config_from_section, get_config
from numpy.distutils.scons.testcode_snippets import cblas_sgemm as cblas_src, \
        c_sgemm as sunperf_src, lapack_sgesv

from support import check_include_and_run, check_symbol
from support import save_and_set, restore, ConfigOpts

def _check(context, name, section, defopts, headers_to_check, funcs_to_check, 
           check_version, version_checker, autoadd):
    context.Message("Checking %s ... " % name)

    # Get site.cfg customization if any
    siteconfig, cfgfiles = get_config()
    (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
    if found:
        opts = ConfigOpts(cpppath = cpppath, libpath = libpath, libs = libs)
    else:
        opts = defopts

    env = context.env

    # Check whether the header is available (CheckHeader-like checker)
    saved = save_and_set(env, opts)
    try:
        # XXX: add dep vars in code
        src = '\n'.join([r'#include <%s>\n' % h for h in headers_to_check])
        st = context.TryCompile(src, '.c')
    finally:
        restore(env, saved)

    if not st:
        context.Result('Failed (could not check header(s) : check config.log '\
                       'in %s for more details)' % env['build_dir'])
        return st, {}

    # Check whether the library is available (CheckLib-like checker)
    saved = save_and_set(env, opts)
    try:
        for sym in funcs_to_check:
            # XXX: add dep vars in code
            st = check_symbol(context, headers_to_check, sym)
            if not st:
                break
    finally:
        if st == 0 or autoadd == 0:
            restore(env, saved)
        
    if not st:
        context.Result('Failed (could not check symbol %s : check config.log '\
                       'in %s for more details))' % (sym, env['build_dir']))
        return st, {}
        
    context.Result(st)

    # Check version if requested
    if check_version:
        if version_checker:
            vst, v = version_checker(env, opts)
            if vst:
                version = v
            else:
                version = 'Unknown (checking version failed)'
        else:
            version = 'Unkown (not implemented)'

    return st, opts

def CheckMKL(context, check_version = 0, autoadd = 1):
    name = 'MKL'
    section = 'mkl'
    defopts = ConfigOpts(libs = ['mkl', 'guide', 'm'])
    headers = ['mkl.h']
    funcs = ['MKLGetVersion']

    def mkl_version_checker(env, opts):
        version_code = r"""
#include <stdio.h>
#include <mkl.h>

int main(void)
{
    MKLVersion ver;
    MKLGetVersion(&ver);

    printf("Full version: %d.%d.%d\n", ver.MajorVersion,
           ver.MinorVersion,
           ver.BuildNumber);

    return 0;
}
"""

        opts['rpath'] = libpath
        saved = save_and_set(env, opts)
        try:
            vst, out = context.TryRun(version_code, '.c')
        finally:
            restore(env, saved)

        if vst and re.search(r'Full version: (\d+[.]\d+[.]\d+)', out):
            version = m.group(1)
        else:
            version = ''

        return vst, version

    return _check(context, name, section, defopts, headers, funcs,
                  check_version, mkl_version_checker, autoadd)

#def CheckMKL(context, check_version = 0, autoadd = 1):
#    """Check whether mkl is usable in C."""
#    context.Message("Checking MKL ... ")
#
#    # XXX: take into account siteconfig
#    section = "mkl"
#    siteconfig, cfgfiles = get_config()
#    (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
#    if not found:
#        # XXX: find exact options to use for the MKL
#        libs.extend(['mkl', 'guide', 'm'])
#    opts = {'cpppath' : cpppath, 'libpath' : libpath, 'libs' : libs} 
#
#    env = context.env
#    test_funcs = ['MKLGetVersion']
#    headers = ['mkl.h']
#
#    # Check whether the header is available (CheckHeader-like checker)
#    saved = save_and_set(env, opts)
#    try:
#        # XXX: add dep vars in code
#        src = '\n'.join([r'#include <%s>\n' % h for h in headers])
#        st = context.TryCompile(src, '.c')
#    finally:
#        restore(env, saved)
#
#    if not st:
#        context.Result('Failed (could not check header(s) : check config.log '\
#                       'in %s for more details)' % env['build_dir'])
#        return st, opts
#
#    # Check whether the library is available (CheckLib-like checker)
#    saved = save_and_set(env, opts)
#    try:
#        for sym in test_funcs:
#            # XXX: add dep vars in code
#            st = check_symbol(context, headers, sym)
#            if not st:
#                break
#    finally:
#        if st == 0 or autoadd == 0:
#            restore(env, saved)
#        
#    if not st:
#        context.Result('Failed (could not check symbol %s : check config.log in %s for more details))' % (sym, env['build_dir']))
#        return st, opts
#        
#    context.Result(st)
#
#    # Check version if requested
#    if check_version:
#        version_code = r"""
##include <stdio.h>
##include <mkl.h>
#
#int main(void)
#{
#    MKLVersion ver;
#    MKLGetVersion(&ver);
#
#    printf("Full version: %d.%d.%d\n", ver.MajorVersion,
#           ver.MinorVersion,
#           ver.BuildNumber);
#
#    return 0;
#}
#"""
#
#        opts['rpath'] = libpath
#        saved = save_and_set(env, opts)
#        try:
#            vst, out = context.TryRun(version_code, '.c')
#        finally:
#            restore(env, saved)
#
#        if not vst:
#            version = r'?.?.? (could not get version)'
#        else:
#            m = re.search(r'Full version: (\d+[.]\d+[.]\d+)', out)
#            if m:
#                version = m.group(1)
#            else:
#                version = r'?.?.? (could not get version)'
#        opts['version'] = version
#
#    return st, opts

def CheckATLAS2(context, check_version = 1, autoadd = 1):
    """Check whether ATLAS is usable in C."""
    name    = 'ATLAS'
    section = 'atlas'
    defopts = ConfigOpts(libs = ['atlas'])
    headers = ['atlas_enum.h']
    funcs   = ['ATL_sgemm']
    return _check(context, name, section, defopts, headers, funcs,
                  check_version, None, autoadd)

#    context.Message("Checking ATLAS ... ")
# 
#    section = "atlas"
#    siteconfig, cfgfiles = get_config()
#    (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
#    if not found:
#        libs.extend(['atlas'])
#    opts = {'cpppath' : cpppath, 'libpath' : libpath, 'libs' : libs}
#
#    env = context.env
#    test_funcs = ['ATL_sgemm']
#    headers = ['atlas_enum.h']
#
#    # Check whether the header is available (CheckHeader-like checker)
#    saved = save_and_set(env, opts)
#    try:
#        # XXX: add dep vars in code
#        src = '\n'.join([r'#include <%s>\n' % h for h in headers])
#        st = context.TryCompile(src, '.c')
#    finally:
#        restore(env, saved)
#
#    if not st:
#        context.Result('Failed (could not check header(s))')
#        return st
#
#    # Check whether the library is available (CheckLib-like checker)
#    saved = save_and_set(env, opts)
#    try:
#        for sym in test_funcs:
#            # XXX: add dep vars in code
#            st = check_symbol(context, headers, sym)
#            if not st:
#                break
#    finally:
#        if st == 0 or autoadd == 0:
#            restore(env, saved)
#        
#    if not st:
#        context.Result('Failed (could not check symbol %s)' % sym)
#        return st
#        
#    context.Result(st)
#
#    # Check version if requested
#    if check_version:
#        saved = save_and_set(env, opts)
#        version_code = """
#void ATL_buildinfo(void);
#int main(void) {
#  ATL_buildinfo();
#  return 0;
#}
#"""
#        try:
#            vst, out = context.TryRun(version_code, '.c')
#        finally:
#            restore(env, saved)
#
#        if not vst:
#            version = r'?.?.? (could not get version)'
#        else:
#            m = re.search(
#                    r'ATLAS version (?P<version>\d+[.]\d+[.]\d+)',
#                    out)
#            if m:
#                version = m.group('version')
#            else:
#                version = r'?.?.? (could not get version)'
#        opts['version'] = version
#
#    return st, opts

def CheckATLAS(context, autoadd = 1):
    """Check whether ATLAS is usable in C."""

    libs = ['atlas', 'f77blas', 'cblas']
    libpath = []

    return check_include_and_run(context, 'ATLAS', None, ['atlas_enum.h', 'cblas.h'],
                                  cblas_src, libs, libpath, [], [], autoadd)

def CheckAccelerate(context, autoadd = 1):
    """Checker for Accelerate framework (on Mac OS X >= 10.3). Only test from
    C."""
    # According to
    # http://developer.apple.com/hardwaredrivers/ve/vector_libraries.html:
    #
    #   This page contains a continually expanding set of vector libraries
    #   that are available to the AltiVec programmer through the Accelerate
    #   framework on MacOS X.3, Panther. On earlier versions of MacOS X,
    #   these were available in vecLib.framework. The currently available
    #   libraries are described below.

    #XXX: get_platform does not seem to work...
    #if get_platform()[-4:] == 'i386':
    #    is_intel = 1
    #    cflags.append('-msse3')
    #else:
    #    is_intel = 0
    #    cflags.append('-faltivec')

    # XXX: This double append is not good, any other way ?
    linkflags = ['-framework', 'Accelerate']

    return check_include_and_run(context, 'FRAMEWORK: Accelerate', None, 
                                  ['Accelerate/Accelerate.h'], cblas_src, [], 
                                  [], linkflags, [], autoadd)

def CheckVeclib(context, autoadd = 1):
    """Checker for Veclib framework (on Mac OS X < 10.3)."""
    # XXX: This double append is not good, any other way ?
    linkflags = ['-framework', 'vecLib']

    return check_include_and_run(context, 'FRAMEWORK: veclib', None, 
                                  ['vecLib/vecLib.h'], cblas_src, [], 
                                  [], linkflags, [], autoadd)

def CheckSunperf(context, autoadd = 1):
    """Checker for sunperf using a simple sunperf example"""

    # XXX: Other options needed ?
    linkflags = ['-xlic_lib=sunperf']
    cflags = ['-dalign']

    return check_include_and_run(context, 'sunperf', None, 
                                  ['sunperf.h'], sunperf_src, [], 
                                  [], linkflags, cflags, autoadd)

