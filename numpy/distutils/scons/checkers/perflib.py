#! /usr/bin/env python
# Last Change: Tue Oct 30 09:00 PM 2007 J

# This module defines checkers for performances libs providing standard API,
# such as MKL (Intel), ATLAS, Sunperf (solaris and linux), Accelerate (Mac OS
# X), etc... Those checkers merely only check whether the library is found
# using a library specific check if possible, or other heuristics.
# Generally, you don't use those directly: they are used in 'meta' checkers,
# such as BLAS, CBLAS, LAPACK checkers.

from numpy.distutils.scons.libinfo import get_config_from_section, get_config
from numpy.distutils.scons.testcode_snippets import cblas_sgemm as cblas_src, \
        c_sgemm as sunperf_src, lapack_sgesv

from support import check_include_and_run, CheckOptions

#def CheckMKL(context, mkl_dir, nb):
#    """mkl_lib is the root path of MKL (the one which contains include, lib,
#    etc...). nb is 32, 64, emt, etc..."""
#
#    libs = ['mkl']
#    cpppath = os.path.join(mkl_dir, 'include')
#    libpath = os.path.join(mkl_dir, 'lib', nb)
#
#    return check_include_and_run(context, 'MKL', cpppath, ['mkl.h'],
#                                  cblas_src, libs, libpath, [], [], autoadd)

#     code = """
# #include <stdio.h>
# #include "mkl.h"
# 
# int main(void)
# {
#     MKLVersion ver;
#     MKLGetVersion(&ver);
# 
#     printf("Major version:          %d\n",ver.MajorVersion);
#     printf("Minor version:          %d\n",ver.MinorVersion);
#     printf("Build number:           %d\n",ver.BuildNumber);
#     printf("Full version: %d.%d.%d\n", 
#            ver.MajorVersion,
#            ver.MinorVersion,
#            ver.BuildNumber);
#     printf("Product status:         %s\n",ver.ProductStatus);
#     printf("Build:                  %s\n",ver.Build);
#     printf("Processor optimization: %s\n",ver.Processor);
# 
#     return 0;
# }
# """

# def CheckMKL(context, autoadd = 1):
#     """Check MKL is usable using a simple cblas example."""
#     section = "mkl"
#     siteconfig, cfgfiles = get_config()
#     (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
#     if not found:
#         # XXX: find exact options to use for the MKL
#         libs.extend(['mkl', 'guide', 'm'])
# 
#     headers = ['mkl.h']
# 
#     return check_include_and_run(context, 'MKL', cpppath, headers,
#                                   cblas_src, libs, libpath, [], [], autoadd)

def _CheckATLASVersion(context):
    pass

from support import save_set, restore
import re

def CheckMKL(context, check_version = 1, autoadd = 1):
    """Check whether mkl is usable in C."""
    context.Message("Checking MKL ... ")

    # XXX: take into account siteconfig
    section = "mkl"
    siteconfig, cfgfiles = get_config()
    (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
    if not found:
        # XXX: find exact options to use for the MKL
        libs.extend(['mkl', 'guide', 'm'])
    opts = {'cpppath' : cpppath, 'libpath' : libpath, 'libs' : libs} 

    env = context.env
    test_funcs = ['MKLGetVersion']
    headers = ['mkl.h']

    # Check whether the header is available (CheckHeader-like checker)
    saved = save_set(env, opts)
    try:
        # XXX: add dep vars in code
        src = '\n'.join([r'#include <%s>\n' % h for h in headers])
        st = context.TryCompile(src, '.c')
    finally:
        restore(env, saved)

    if not st:
        context.Result('Failed (could not check header(s))')
        return st

    # Check whether the library is available (CheckLib-like checker)
    saved = save_set(env, opts)
    try:
        for sym in test_funcs:
            # XXX: add dep vars in code
            st = check_symbol(context, headers, sym)
            if not st:
                break
    finally:
        if st == 0 or autoadd == 0:
            restore(env, saved)
        
    if not st:
        context.Result('Failed (could not check symbol %s)' % sym)
        return st
        
    context.Result(st)

    # Check version if requested
    if check_version:
        saved = save_set(env, opts)
        version_code = """
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

        try:
            vst, out = context.TryRun(version_code, '.c')
        finally:
            restore(env, saved)

        if not vst:
            version = r'?.?.? (could not get version)'
        else:
            m = re.search(
                    r'Full version: (\d+[.]\d+[.]\d+)',
                    out)
            if m:
                version = m.group('version')
            else:
                version = r'?.?.? (could not get version)'
        opts['version'] = version

    return st, opts

def check_symbol(context, headers, sym, extra = r''):
    # XXX: add dep vars in code
    code = [r'#include <%s>' %h for h in headers]
    code.append(r'''
#undef %(func)s
#ifdef __cplusplus
extern "C" 
#endif
char %(func)s();

int main()
{
return %(func)s();
return 0;
}
''' % {'func' : sym})
    code.append(extra)
    return context.TryLink('\n'.join(code), '.c')

def CheckATLAS2(context, check_version = 1, autoadd = 1):
    """Check whether ATLAS is usable in C."""
    context.Message("Checking ATLAS ... ")

    section = "atlas"
    siteconfig, cfgfiles = get_config()
    (cpppath, libs, libpath), found = get_config_from_section(siteconfig, section)
    if not found:
        libs.extend(['atlas'])
    opts = {'cpppath' : cpppath, 'libpath' : libpath, 'libs' : libs}

    env = context.env
    test_funcs = ['ATL_sgemm']
    headers = ['atlas_enum.h']

    # Check whether the header is available (CheckHeader-like checker)
    saved = save_set(env, opts)
    try:
        # XXX: add dep vars in code
        src = '\n'.join([r'#include <%s>\n' % h for h in headers])
        st = context.TryCompile(src, '.c')
    finally:
        restore(env, saved)

    if not st:
        context.Result('Failed (could not check header(s))')
        return st

    # Check whether the library is available (CheckLib-like checker)
    saved = save_set(env, opts)
    try:
        for sym in test_funcs:
            # XXX: add dep vars in code
            st = check_symbol(context, headers, sym)
            if not st:
                break
    finally:
        if st == 0 or autoadd == 0:
            restore(env, saved)
        
    if not st:
        context.Result('Failed (could not check symbol %s)' % sym)
        return st
        
    context.Result(st)

    # Check version if requested
    if check_version:
        saved = save_set(env, opts)
        version_code = """
void ATL_buildinfo(void);
int main(void) {
  ATL_buildinfo();
  return 0;
}
"""
        try:
            vst, out = context.TryRun(version_code, '.c')
        finally:
            restore(env, saved)

        if not vst:
            version = r'?.?.? (could not get version)'
        else:
            m = re.search(
                    r'ATLAS version (?P<version>\d+[.]\d+[.]\d+)',
                    out)
            if m:
                version = m.group('version')
            else:
                version = r'?.?.? (could not get version)'
        opts['version'] = version

    return st, opts

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

