#ifndef _NPY_INTERNAL_ARRAYOBJECT_H_
#define _NPY_INTERNAL_ARRAYOBJECT_H_

#ifndef _MULTIARRAYMODULE
#error You should not include this
#endif

NPY_NO_EXPORT PyObject *
_strings_richcompare(PyArrayObject *self, PyArrayObject *other, int cmp_op,
                     int rstrip);

NPY_NO_EXPORT PyObject *
array_richcompare(PyArrayObject *self, PyObject *other, int cmp_op);

/* AUX data used by array_sort / array_argsort and VOID_compare */
typedef struct {
    struct NpyAuxData_tag base;
    npy_intp n_fields;
    int * flags;
    npy_intp * offsets;
    PyArray_Descr ** descrs;
} SortOrderAuxData;

NPY_NO_EXPORT NpyAuxData * 
sort_order_aux_data_clone(NpyAuxData * p);

NPY_NO_EXPORT SortOrderAuxData * 
sort_order_aux_data_alloc(npy_intp n_fields);

NPY_NO_EXPORT void 
sort_order_aux_data_free(NpyAuxData * p);

NPY_NO_EXPORT int
array_might_be_written(PyArrayObject *obj);

/*
 * This flag is used to mark arrays which we would like to, in the future,
 * turn into views. It causes a warning to be issued on the first attempt to
 * write to the array (but the write is allowed to succeed).
 *
 * This flag is for internal use only, and may be removed in a future release,
 * which is why the #define is not exposed to user code. Currently it is set
 * on arrays returned by ndarray.diagonal.
 */
static const int NPY_ARRAY_WARN_ON_WRITE = (1 << 31);

#endif
