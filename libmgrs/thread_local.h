#ifndef MGRS_THREAD_LOCAL_H
#define MGRS_THREAD_LOCAL_H

/*
 * The GeoTrans projection routines keep their active parameters in file-scope
 * variables.  ctypes releases Python's GIL while calling these routines, so
 * process-global parameters allow concurrent conversions to overwrite one
 * another.  Keep the existing C API while giving each calling thread an
 * independent parameter set.
 *
 * C11 and modern MSVC both provide native thread-local storage.  GCC's
 * __thread is retained as a fallback for older Unix compilers supported by
 * this library.
 */
#if defined(_MSC_VER)
#  define MGRS_THREAD_LOCAL __declspec(thread)
#elif defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
#  define MGRS_THREAD_LOCAL _Thread_local
#elif defined(__GNUC__) || defined(__clang__)
#  define MGRS_THREAD_LOCAL __thread
#else
#  error "libmgrs requires compiler support for thread-local storage"
#endif

#endif /* MGRS_THREAD_LOCAL_H */
