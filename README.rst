.. _home:

mgrs: Converting to and from MGRS and Decimal Degrees
------------------------------------------------------------------------------

GeoTrans_ provides C code for converting to and from MGRS, but well, it's
C code :).  This is a simple ctypes_ wrapper around two of the MGRS-related
functions in GeoTrans_.

This library has an internal copy of some of the files from GeoTrans_ 2.4.2.

.. _`GeoTrans`: http://earth-info.nga.mil/GandG/geotrans/
.. _`ctypes`: http://docs.python.org/library/ctypes.html



ChangeLog
------------------------------------------------------------------------------

1.5.3

* Fix busted auto-release

1.5.2

* Use ABI name for finding DLL

1.5.1

* Wheels
* fix broken test with fixed precision comparison

1.5.0

* Wheels
* pyproject.toml-based metadata

1.4.3

* Wheels
* black, flake8, and isort linters

1.4.2

* GitHub Action builders needed to be changed to push release

1.4.1

* Fix install requirements #34

1.4.0

* Alias and deprecate RTreeError #33

1.3.9

* MGRS now requires packaging library #31
* Fix wheel imports of shared libs

1.3.8

* UTF-8 encoding for all strings.
* Fix #29 implicit tuple on return of UTMToMGRS

1.3.7

* automated building of osx, linux and win64 wheels
* Migrate from TravisCI => GitHub Actions
* Warnings cleanup
* flake8 validation

1.3.6

* required positional argument for wheel.425tags.get_platform()
  https://github.com/hobu/mgrs/pull/24

1.3.4

* Truncate, don't round results https://github.com/hobu/mgrs/pull/15
* Apply license

1.3.3

* SOABI support #10 https://github.com/hobu/mgrs/pull/10
* Clean up some compilation warnings
* Travis builds https://travis-ci.org/hobu/mgrs

1.3.2

* Better Windows support
* Bug fix for 3 digit longitudes

1.3.1

* Python 3.x support
* Allow user to override precision in UTMToMGRS


Usage
------------------------------------------------------------------------------

In a nutshell::

    >>> import mgrs

    >>> latitude = 42.0
    >>> longitude = -93.0

    >>> m = mgrs.MGRS()
    >>> c = m.toMGRS(latitude, longitude)
    >>> c
    '15TWG0000049776'

    >>> d = m.toLatLon(c)
    >>> d
    (41.999997975127997, -93.000000000000014)

    >>> y = '321942.29N'
    >>> yd = m.dmstodd(y)
    32.328414

    >>> d, m, s = m.ddtodms(32.328414)
    >>> d, m, s
    (32.0, 19.0, 42.290400)

You can also control the precision of the MGRS grid with the MGRSPrecision
arguments in .toMGRS().  Other than that, there isn't too much to it.


Thread safety
------------------------------------------------------------------------------

Native projection parameters are stored per operating-system thread.  Calls on
different threads can therefore overlap without changing one another's active
MGRS, UTM, UPS, Transverse Mercator, or Polar Stereographic parameters.  The
module exposes ``THREAD_SAFE`` and ``THREAD_SAFETY_IMPLEMENTATION`` capability
markers so applications can detect this behavior.

The native ``Set_*_Parameters`` and ``Get_*_Parameters`` C functions now have
thread-local semantics: a setter changes only the calling thread's parameter
set, and a getter reads that same thread's parameter set.  Code that selects a
non-default ellipsoid directly through the C API must call its setter in every
worker thread that uses it.  Function signatures and single-threaded behavior
are unchanged.

Conversion status
------------------------------------------------------------------------------

``MGRSToUTMWithStatus`` provides an inverse conversion without emitting Python
warnings::

    >>> result, status = mgrs.MGRS().MGRSToUTMWithStatus("50TMK5045027900")
    >>> result
    (50, 'N', 450450.0, 4427900.0)
    >>> bool(status & mgrs.MGRS_LAT_WARNING)
    True

Hard conversion errors still raise ``MGRSError``.  Warning bits are returned
in ``status`` so concurrent applications do not need to alter process-global
``warnings`` filters.  The existing ``MGRSToUTM`` method retains its historical
warning behavior.
