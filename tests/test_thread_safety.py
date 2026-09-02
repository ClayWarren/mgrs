import ctypes
import math
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import mgrs
from mgrs import core

POINTS = (
    (42.0, -93.0),
    (38.9072, -77.0369),
    (39.9998, 116.4195),
    (-33.8688, 151.2093),
    (60.3913, 5.3221),
    (78.2232, 15.6469),
    (1.3521, 103.8198),
    (-34.6037, -58.3816),
    (89.0, 0.0),
    (-89.0, 120.0),
)


def test_native_thread_safety_capability_marker():
    assert mgrs.THREAD_SAFE is True
    assert mgrs.THREAD_SAFETY_IMPLEMENTATION == "native-thread-local-state-v1"


def test_mixed_zone_utm_ups_conversions_match_serial_oracle_under_stress():
    serial = mgrs.MGRS()
    oracle = tuple(
        (point, serial.toMGRS(*point), serial.toLatLon(serial.toMGRS(*point)))
        for point in POINTS
    )
    # Duplicate every case so same-input and mixed-input calls overlap.  The
    # pre-fix implementation reliably returned wrong cells and Easting Error
    # exceptions under this synchronized workload.
    cases = oracle + oracle
    barrier = Barrier(len(cases))

    def exercise(case):
        point, expected_mgrs, expected_latlon = case
        converter = mgrs.MGRS()
        failure = None
        for _ in range(2_000):
            barrier.wait(timeout=30)
            try:
                actual_mgrs = converter.toMGRS(*point)
            except Exception as error:  # pragma: no cover - regression detail
                if failure is None:
                    failure = (point, "forward error", repr(error))
            else:
                if actual_mgrs != expected_mgrs and failure is None:
                    failure = (
                        point,
                        "forward mismatch",
                        actual_mgrs,
                        expected_mgrs,
                    )
            barrier.wait(timeout=30)
            try:
                actual_latlon = converter.toLatLon(expected_mgrs)
            except Exception as error:  # pragma: no cover - regression detail
                if failure is None:
                    failure = (point, "inverse error", repr(error))
            else:
                if actual_latlon != expected_latlon and failure is None:
                    failure = (
                        point,
                        "inverse mismatch",
                        actual_latlon,
                        expected_latlon,
                    )
        return failure

    with ThreadPoolExecutor(max_workers=len(cases)) as executor:
        futures = [executor.submit(exercise, case) for case in cases]
        failures = [future.result(timeout=60) for future in futures]

    assert [failure for failure in failures if failure is not None] == []


def test_public_parameter_state_is_thread_local():
    _configure_parameter_function_signatures()
    workers = 8
    barriers = [Barrier(workers) for _ in range(5)]

    def exercise(index):
        a = 6_378_137.0 + index
        f = 1.0 / (298.257223563 + index / 100.0)
        code = f"{index:02d}".encode("ascii")

        assert core.rt.Set_MGRS_Parameters(a, f, code) == 0
        barriers[0].wait(timeout=30)
        got_a = ctypes.c_double()
        got_f = ctypes.c_double()
        got_code = ctypes.create_string_buffer(3)
        mgrs_outputs = (ctypes.byref(got_a), ctypes.byref(got_f), got_code)
        core.rt.Get_MGRS_Parameters(*mgrs_outputs)
        assert (got_a.value, got_f.value, got_code.value) == (a, f, code)

        override = index + 1
        assert core.rt.Set_UTM_Parameters(a, f, override) == 0
        barriers[1].wait(timeout=30)
        got_override = ctypes.c_long()
        utm_outputs = (
            ctypes.byref(got_a),
            ctypes.byref(got_f),
            ctypes.byref(got_override),
        )
        core.rt.Get_UTM_Parameters(*utm_outputs)
        actual_utm_parameters = (got_a.value, got_f.value, got_override.value)
        assert actual_utm_parameters == (a, f, override)

        assert core.rt.Set_UPS_Parameters(a, f) == 0
        barriers[2].wait(timeout=30)
        core.rt.Get_UPS_Parameters(ctypes.byref(got_a), ctypes.byref(got_f))
        assert (got_a.value, got_f.value) == (a, f)

        central_meridian = math.radians(-21.0 + index * 6.0)
        false_easting = 500_000.0 + index
        false_northing = 1_000.0 + index
        scale = 0.9996
        assert (
            core.rt.Set_Transverse_Mercator_Parameters(
                a,
                f,
                0.0,
                central_meridian,
                false_easting,
                false_northing,
                scale,
            )
            == 0
        )
        barriers[3].wait(timeout=30)
        origin_latitude = ctypes.c_double()
        got_central_meridian = ctypes.c_double()
        got_false_easting = ctypes.c_double()
        got_false_northing = ctypes.c_double()
        got_scale = ctypes.c_double()
        core.rt.Get_Transverse_Mercator_Parameters(
            ctypes.byref(got_a),
            ctypes.byref(got_f),
            ctypes.byref(origin_latitude),
            ctypes.byref(got_central_meridian),
            ctypes.byref(got_false_easting),
            ctypes.byref(got_false_northing),
            ctypes.byref(got_scale),
        )
        assert (
            got_a.value,
            got_f.value,
            origin_latitude.value,
            got_central_meridian.value,
            got_false_easting.value,
            got_false_northing.value,
            got_scale.value,
        ) == (
            a,
            f,
            0.0,
            central_meridian,
            false_easting,
            false_northing,
            scale,
        )

        true_scale_latitude = math.radians(70.0 + index / 10.0)
        down_from_pole = math.radians(index)
        assert (
            core.rt.Set_Polar_Stereographic_Parameters(
                a,
                f,
                true_scale_latitude,
                down_from_pole,
                false_easting,
                false_northing,
            )
            == 0
        )
        barriers[4].wait(timeout=30)
        got_true_scale_latitude = ctypes.c_double()
        got_down_from_pole = ctypes.c_double()
        core.rt.Get_Polar_Stereographic_Parameters(
            ctypes.byref(got_a),
            ctypes.byref(got_f),
            ctypes.byref(got_true_scale_latitude),
            ctypes.byref(got_down_from_pole),
            ctypes.byref(got_false_easting),
            ctypes.byref(got_false_northing),
        )
        assert (
            got_a.value,
            got_f.value,
            got_true_scale_latitude.value,
            got_down_from_pole.value,
            got_false_easting.value,
            got_false_northing.value,
        ) == (
            a,
            f,
            true_scale_latitude,
            down_from_pole,
            false_easting,
            false_northing,
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for index in range(workers):
            futures.append(executor.submit(exercise, index))
        for future in futures:
            future.result(timeout=30)


def _configure_parameter_function_signatures():
    core.rt.Set_MGRS_Parameters.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_char_p,
    ]
    core.rt.Set_MGRS_Parameters.restype = ctypes.c_long
    core.rt.Get_MGRS_Parameters.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_char_p,
    ]
    core.rt.Get_MGRS_Parameters.restype = None

    core.rt.Set_UTM_Parameters.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_long,
    ]
    core.rt.Set_UTM_Parameters.restype = ctypes.c_long
    core.rt.Get_UTM_Parameters.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_long),
    ]
    core.rt.Get_UTM_Parameters.restype = None

    core.rt.Set_UPS_Parameters.argtypes = [ctypes.c_double, ctypes.c_double]
    core.rt.Set_UPS_Parameters.restype = ctypes.c_long
    core.rt.Get_UPS_Parameters.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    core.rt.Get_UPS_Parameters.restype = None

    core.rt.Set_Transverse_Mercator_Parameters.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
    ]
    core.rt.Set_Transverse_Mercator_Parameters.restype = ctypes.c_long
    core.rt.Get_Transverse_Mercator_Parameters.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    core.rt.Get_Transverse_Mercator_Parameters.restype = None

    core.rt.Set_Polar_Stereographic_Parameters.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
    ]
    core.rt.Set_Polar_Stereographic_Parameters.restype = ctypes.c_long
    core.rt.Get_Polar_Stereographic_Parameters.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    core.rt.Get_Polar_Stereographic_Parameters.restype = None
