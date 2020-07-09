"""Implementation of __array_function__ overrides from NEP-18."""
import collections
import functools
import os
import textwrap
import inspect

from numpy.core._multiarray_umath import (
    add_docstring, implement_array_function, _get_implementing_args)


ARRAY_FUNCTION_ENABLED = bool(
    int(os.environ.get('NUMPY_EXPERIMENTAL_ARRAY_FUNCTION', 1)))


add_docstring(
    implement_array_function,
    """
    Implement a function with checks for __array_function__ overrides.

    All arguments are required, and can only be passed by position.

    Parameters
    ----------
    implementation : function
        Function that implements the operation on NumPy array without
        overrides when called like ``implementation(*args, **kwargs)``.
    public_api : function
        Function exposed by NumPy's public API originally called like
        ``public_api(*args, **kwargs)`` on which arguments are now being
        checked.
    relevant_args : iterable
        Iterable of arguments to check for __array_function__ methods.
    args : tuple
        Arbitrary positional arguments originally passed into ``public_api``.
    kwargs : dict
        Arbitrary keyword arguments originally passed into ``public_api``.

    Returns
    -------
    Result from calling ``implementation()`` or an ``__array_function__``
    method, as appropriate.

    Raises
    ------
    TypeError : if no implementation is found.
    """)


# exposed for testing purposes; used internally by implement_array_function
add_docstring(
    _get_implementing_args,
    """
    Collect arguments on which to call __array_function__.

    Parameters
    ----------
    relevant_args : iterable of array-like
        Iterable of possibly array-like arguments to check for
        __array_function__ methods.

    Returns
    -------
    Sequence of arguments with __array_function__ methods, in the order in
    which they should be called.
    """)


def verify_matching_signatures(implementation, dispatcher):
    """Verify that a dispatcher function has the right signature."""
    # Get an ordered dict of Parameter objects from each signature
    implementation_sig = inspect.signature(implementation).parameters
    dispatcher_sig = inspect.signature(dispatcher).parameters

    for p1, p2 in zip(implementation_sig.values(), dispatcher_sig.values()):
        if (
            (p1.name != p2.name) or (p1.kind != p2.kind) or
            ((p1.default is p1.empty) and (p2.default is not p2.empty))
        ):
            raise RuntimeError(
                f'implementation and dispatcher for {implementation} have '
                 'different function signatures'
            )
        if (p1.default is not p1.empty) and (p2.default is not None):
            raise RuntimeError(
                f'dispatcher functions can only use None for default '
                 'argument values'
            )


def set_module(module):
    """Decorator for overriding __module__ on a function or class.

    Example usage::

        @set_module('numpy')
        def example():
            pass

        assert example.__module__ == 'numpy'
    """
    def decorator(func):
        if module is not None:
            func.__module__ = module
        return func
    return decorator



# Call textwrap.dedent here instead of in the function so as to avoid
# calling dedent multiple times on the same text
_wrapped_func_source = textwrap.dedent("""
    @functools.wraps(implementation)
    def {name}(*args, **kwargs):
        relevant_args = dispatcher(*args, **kwargs)
        return implement_array_function(
            implementation, {name}, relevant_args, args, kwargs)
    """)


def array_function_dispatch(dispatcher, module=None, verify=True,
                            docs_from_dispatcher=False):
    """Decorator for adding dispatch with the __array_function__ protocol.

    See NEP-18 for example usage.

    Parameters
    ----------
    dispatcher : callable
        Function that when called like ``dispatcher(*args, **kwargs)`` with
        arguments from the NumPy function call returns an iterable of
        array-like arguments to check for ``__array_function__``.
    module : str, optional
        __module__ attribute to set on new function, e.g., ``module='numpy'``.
        By default, module is copied from the decorated function.
    verify : bool, optional
        If True, verify the that the signature of the dispatcher and decorated
        function signatures match exactly: all required and optional arguments
        should appear in order with the same names, but the default values for
        all optional arguments should be ``None``. Only disable verification
        if the dispatcher's signature needs to deviate for some particular
        reason, e.g., because the function has a signature like
        ``func(*args, **kwargs)``.
    docs_from_dispatcher : bool, optional
        If True, copy docs from the dispatcher function onto the dispatched
        function, rather than from the implementation. This is useful for
        functions defined in C, which otherwise don't have docstrings.

    Returns
    -------
    Function suitable for decorating the implementation of a NumPy function.
    """

    if not ARRAY_FUNCTION_ENABLED:
        def decorator(implementation):
            if docs_from_dispatcher:
                add_docstring(implementation, dispatcher.__doc__)
            if module is not None:
                implementation.__module__ = module
            return implementation
        return decorator

    def decorator(implementation):
        if verify:
            verify_matching_signatures(implementation, dispatcher)

        if docs_from_dispatcher:
            add_docstring(implementation, dispatcher.__doc__)

        # Equivalently, we could define this function directly instead of using
        # exec. This version has the advantage of giving the helper function a
        # more interpettable name. Otherwise, the original function does not
        # show up at all in many cases, e.g., if it's written in C or if the
        # dispatcher gets an invalid keyword argument.
        source = _wrapped_func_source.format(name=implementation.__name__)

        source_object = compile(
            source, filename='<__array_function__ internals>', mode='exec')
        scope = {
            'implementation': implementation,
            'dispatcher': dispatcher,
            'functools': functools,
            'implement_array_function': implement_array_function,
        }
        exec(source_object, scope)

        public_api = scope[implementation.__name__]

        if module is not None:
            public_api.__module__ = module

        public_api._implementation = implementation

        return public_api

    return decorator


def array_function_from_dispatcher(
        implementation, module=None, verify=True, docs_from_dispatcher=True):
    """Like array_function_dispatcher, but with function arguments flipped."""

    def decorator(dispatcher):
        return array_function_dispatch(
            dispatcher, module, verify=verify,
            docs_from_dispatcher=docs_from_dispatcher)(implementation)
    return decorator
