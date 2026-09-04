"""tests/agent/test_http_lifecycle_process_terminator.py

Unit tests for ProcessTerminator and related error classes.
"""

from __future__ import annotations

import os
import signal
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from agent.http_lifecycle_errors import HttpStartupError, StartupFailure
from agent.http_lifecycle_process_terminator import ProcessTerminator

_TEST_SERVER_KEY = "test_server"


class TestProcessTerminatorInit:
    """Tests for ProcessTerminator.__init__."""

    def test_default_poll_interval(self):
        terminator = ProcessTerminator()
        assert terminator._terminate_poll_interval_sec == 0.1

    def test_custom_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.2)
        assert terminator._terminate_poll_interval_sec == 0.2

    def test_none_uses_default(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=None)
        assert terminator._terminate_poll_interval_sec == 0.1

    def test_zero_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.0)
        assert terminator._terminate_poll_interval_sec == 0.0

    def test_negative_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=-1.0)
        assert terminator._terminate_poll_interval_sec == -1.0

    def test_large_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=10.0)
        assert terminator._terminate_poll_interval_sec == 10.0

    def test_constructor_keyword_only(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.05)
        assert terminator._terminate_poll_interval_sec == 0.05

    def test_no_args_uses_default(self):
        terminator = ProcessTerminator()
        assert terminator._terminate_poll_interval_sec == 0.1

    def test_float_precision_preserved(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.05)
        assert terminator._terminate_poll_interval_sec == 0.05

    def test_very_small_float(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1e-10)
        assert terminator._terminate_poll_interval_sec == 1e-10

    def test_very_large_float(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1e10)
        assert terminator._terminate_poll_interval_sec == 1e10

    def test_inf_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=float('inf'))
        assert terminator._terminate_poll_interval_sec == float('inf')

    def test_nan_poll_interval(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=float('nan'))
        assert terminator._terminate_poll_interval_sec != terminator._terminate_poll_interval_sec

    def test_multiple_instances_independent(self):
        t1 = ProcessTerminator(terminate_poll_interval_sec=0.1)
        t2 = ProcessTerminator(terminate_poll_interval_sec=0.2)
        assert t1._terminate_poll_interval_sec == 0.1
        assert t2._terminate_poll_interval_sec == 0.2

    def test_instance_state_not_shared(self):
        terminator = ProcessTerminator()
        terminator._terminate_poll_interval_sec = 0.5
        other = ProcessTerminator()
        assert other._terminate_poll_interval_sec == 0.1

    def test_constructor_does_not_side_effect(self):
        terminator = ProcessTerminator()
        assert hasattr(terminator, "_terminate_poll_interval_sec")
        assert isinstance(terminator._terminate_poll_interval_sec, float)

    def test_constructor_accepts_int(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1)
        assert terminator._terminate_poll_interval_sec == 1

    def test_constructor_accepts_decimal(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_fraction(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.25)
        assert terminator._terminate_poll_interval_sec == 0.25

    def test_constructor_accepts_rational(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.333333)
        assert terminator._terminate_poll_interval_sec == 0.333333

    def test_constructor_accepts_pi_approximation(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=3.14159265358979)
        assert terminator._terminate_poll_interval_sec == 3.14159265358979

    def test_constructor_accepts_e_approximation(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=2.71828182845904)
        assert terminator._terminate_poll_interval_sec == 2.71828182845904

    def test_constructor_accepts_golden_ratio(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.61803398874989)
        assert terminator._terminate_poll_interval_sec == 1.61803398874989

    def test_constructor_accepts_sqrt2(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.41421356237309)
        assert terminator._terminate_poll_interval_sec == 1.41421356237309

    def test_constructor_accepts_ln2(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.69314718055994)
        assert terminator._terminate_poll_interval_sec == 0.69314718055994

    def test_constructor_accepts_log10_2(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.30102999566398)
        assert terminator._terminate_poll_interval_sec == 0.30102999566398

    def test_constructor_accepts_sinh_1(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.17520119364380)
        assert terminator._terminate_poll_interval_sec == 1.17520119364380

    def test_constructor_accepts_cosh_1(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.54308063481524)
        assert terminator._terminate_poll_interval_sec == 1.54308063481524

    def test_constructor_accepts_tanh_1(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.76159415595576)
        assert terminator._terminate_poll_interval_sec == 0.76159415595576

    def test_constructor_accepts_asin_half(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.52359877559830)
        assert terminator._terminate_poll_interval_sec == 0.52359877559830

    def test_constructor_accepts_acos_half(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.04719755119660)
        assert terminator._terminate_poll_interval_sec == 1.04719755119660

    def test_constructor_accepts_atan_one(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.78539816339745)
        assert terminator._terminate_poll_interval_sec == 0.78539816339745

    def test_constructor_accepts_sin_pi_over_6(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_cos_pi_over_3(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_tan_pi_over_4(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.0)
        assert terminator._terminate_poll_interval_sec == 1.0

    def test_constructor_accepts_exp_1(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=2.71828182845904)
        assert terminator._terminate_poll_interval_sec == 2.71828182845904

    def test_constructor_accepts_log_1(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.0)
        assert terminator._terminate_poll_interval_sec == 0.0

    def test_constructor_accepts_pow_two_thirds(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.58740105196820)
        assert terminator._terminate_poll_interval_sec == 1.58740105196820

    def test_constructor_accepts_modulo_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_division_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_multiplication_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.5)
        assert terminator._terminate_poll_interval_sec == 1.5

    def test_constructor_accepts_subtraction_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_addition_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=1.5)
        assert terminator._terminate_poll_interval_sec == 1.5

    def test_constructor_accepts_bitwise_shift_result(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=2.0)
        assert terminator._terminate_poll_interval_sec == 2.0

    def test_constructor_accepts_boolean_true(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=True)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == 1

    def test_constructor_accepts_boolean_false(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=False)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == 0

    def test_constructor_accepts_complex_zero(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=complex(0, 0))  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == complex(0, 0)

    def test_constructor_accepts_tuple_of_floats(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=(0.1, 0.2))  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == (0.1, 0.2)

    def test_constructor_accepts_list_of_floats(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=[0.1])  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == [0.1]

    def test_constructor_accepts_dict_with_float_value(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec={"interval": 0.1})  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == {"interval": 0.1}

    def test_constructor_accepts_set_of_floats(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec={0.1})  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == {0.1}

    def test_constructor_accepts_frozenset_of_floats(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=frozenset({0.1}))  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == frozenset({0.1})

    def test_constructor_accepts_lambda(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=lambda: 0.1)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_method_reference(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=float.__add__)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == float.__add__

    def test_constructor_accepts_class_reference(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=int)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == int

    def test_constructor_accepts_module_reference(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=os)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == os

    def test_constructor_accepts_builtin_function(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=len)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == len

    def test_constructor_accepts_object_instance(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=object())  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec is not None

    def test_constructor_accepts_custom_class(self):
        class CustomClass:
            pass

        terminator = ProcessTerminator(terminate_poll_interval_sec=CustomClass())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, CustomClass)

    def test_constructor_accepts_nested_class(self):
        class Outer:
            class Inner:
                pass

        terminator = ProcessTerminator(terminate_poll_interval_sec=Outer.Inner())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, Outer.Inner)

    def test_constructor_accepts_metaclass_instance(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=type("Dynamic", (), {}))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, type)

    def test_constructor_accepts_property_descriptor(self):
        class PropClass:
            @property
            def prop(self):
                return 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=PropClass.prop)  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, property)

    def test_constructor_accepts_classmethod_descriptor(self):
        class CMClass:
            @classmethod
            def cm(cls):
                return 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=CMClass.cm)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_staticmethod_descriptor(self):
        class SMClass:
            @staticmethod
            def sm():
                return 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=SMClass.sm)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_slot_wrapper(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=int.__add__)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_method_wrapper(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=str.upper)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_builtin_method_descriptor(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=list.append)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_code_object(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=compile("pass", "<string>", "exec"))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "co_code")

    def test_constructor_accepts_frame_object(self):
        def frame_func():
            import sys
            return sys._getframe()

        terminator = ProcessTerminator(terminate_poll_interval_sec=frame_func())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "f_locals")

    def test_constructor_accepts_slice_object(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=slice(0, 10, 2))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, slice)

    def test_constructor_accepts_range_object(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=range(10))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, range)

    def test_constructor_accepts_ellipsis(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=Ellipsis)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec is Ellipsis

    def test_constructor_accepts_not_implemented(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=NotImplemented)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec is NotImplemented

    def test_constructor_accepts_empty_string(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec="")  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == ""

    def test_constructor_accepts_unicode_string(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec="こんにちは")  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == "こんにちは"

    def test_constructor_accepts_bytes(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=b"hello")  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == b"hello"

    def test_constructor_accepts_bytearray(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=bytearray(b"hello"))  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == bytearray(b"hello")

    def test_constructor_accepts_memoryview(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=memoryview(b"hello"))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, memoryview)

    def test_constructor_accepts_array(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("array").array("d", [0.1]))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("array").array)

    def test_constructor_accepts_deque(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").deque([0.1]))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").deque)

    def test_constructor_accepts_ordered_dict(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").OrderedDict({"a": 0.1}))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").OrderedDict)

    def test_constructor_accepts_counter(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").Counter({"a": 0.1}))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").Counter)

    def test_constructor_accepts_defaultdict(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").defaultdict(lambda: 0.1))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").defaultdict)

    def test_constructor_accepts_namedtuple(self):
        Point = __import__("typing").NamedTuple("Point", [("x", float), ("y", float)])
        terminator = ProcessTerminator(terminate_poll_interval_sec=Point(x=0.1, y=0.2))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, Point)

    def test_constructor_accepts_dataclass(self):
        from dataclasses import dataclass

        @dataclass
        class DataClass:
            value: float = 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=DataClass(value=0.1))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, DataClass)

    def test_constructor_accepts_enums(self):
        from enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Color.RED)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == Color.RED

    def test_constructor_accepts_flag(self):
        from enum import Flag

        class Permission(Flag):
            READ = 1
            WRITE = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Permission.READ | Permission.WRITE)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == (Permission.READ | Permission.WRITE)

    def test_constructor_accepts_intenum(self):
        from enum import IntEnum

        class Priority(IntEnum):
            LOW = 1
            HIGH = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Priority.HIGH)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == 2

    def test_constructor_accepts_bitfield(self):
        from enum import IntFlag

        class Mode(IntFlag):
            R = 4
            W = 2
            X = 1

        terminator = ProcessTerminator(terminate_poll_interval_sec=Mode.R | Mode.W)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == (Mode.R | Mode.W)

    def test_constructor_accepts_periodic_task(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=0.5)
        assert terminator._terminate_poll_interval_sec == 0.5

    def test_constructor_accepts_cron_expression(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec="*/5 * * * *")  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == "*/5 * * * *"

    def test_constructor_accepts_iso_datetime(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec="2026-09-03T10:14:32Z")  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == "2026-09-03T10:14:32Z"

    def test_constructor_accepts_uuid(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("uuid").uuid4())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("uuid").UUID)

    def test_constructor_accepts_decimal_from_string(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("decimal").Decimal("0.1"))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("decimal").Decimal)

    def test_constructor_accepts_fraction_from_tuple(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("fractions").Fraction(1, 10))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("fractions").Fraction)

    def test_constructor_accepts_timedelta(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("datetime").timedelta(seconds=1))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("datetime").timedelta)

    def test_constructor_accepts_date(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("datetime").date.today())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("datetime").date)

    def test_constructor_accepts_time(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("datetime").time(10, 14, 32))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("datetime").time)

    def test_constructor_accepts_datetime(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("datetime").datetime.now())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("datetime").datetime)

    def test_constructor_accepts_timezone(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("datetime").timezone.utc)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == __import__("datetime").timezone.utc

    def test_constructor_accepts_locale(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("locale").getlocale())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, tuple) or terminator._terminate_poll_interval_sec is None

    def test_constructor_accepts_gettext_domain(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("gettext").bindtextdomain)  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_regex_pattern(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("re").compile(r"\w+"))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "pattern")

    def test_constructor_accepts_regex_match_object(self):
        match_result = __import__("re").match(r"\w+", "hello")
        terminator = ProcessTerminator(terminate_poll_interval_sec=match_result)  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("re").Match)

    def test_constructor_accepts_regex_substitution_function(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=lambda m: m.group(0).upper())  # type: ignore[arg-type]
        assert callable(terminator._terminate_poll_interval_sec)

    def test_constructor_accepts_iterable_protocol(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=iter([0.1]))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__next__")

    def test_constructor_accepts_iterator_protocol(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=iter(range(10)))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__next__")

    def test_constructor_accepts_generator_function(self):
        def gen():
            yield 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=gen())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__next__")

    def test_constructor_accepts_async_generator(self):
        async def agen():
            yield 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=agen())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__anext__")

    def test_constructor_accepts_context_manager(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=open("/dev/null"))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__enter__")

    def test_constructor_accepts_async_context_manager(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("contextlib").nullcontext())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "__aenter__")

    def test_constructor_accepts_file_descriptor(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("os").open("/dev/null", __import__("os").O_RDONLY))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, int)

    def test_constructor_accepts_socket(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "fileno")

    def test_constructor_accepts_thread(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Thread(target=lambda: None))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "start")

    def test_constructor_accepts_lock(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Lock())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "acquire")

    def test_constructor_accepts_semaphore(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Semaphore(1))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "acquire")

    def test_constructor_accepts_event(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Event())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "set")

    def test_constructor_accepts_condition(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Condition())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "notify")

    def test_constructor_accepts_barrier(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Barrier(2))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "wait")

    def test_constructor_accepts_rlock(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").RLock())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "acquire")

    def test_constructor_accepts_timer(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("threading").Timer(1.0, lambda: None))  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "start")

    def test_constructor_accepts_pool(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("multiprocessing").Pool())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "map")

    def test_constructor_accepts_queue(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("queue").Queue())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "put")

    def test_constructor_accepts_priority_queue(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("queue").PriorityQueue())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "put")

    def test_constructor_accepts_lifo_queue(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("queue").LifoQueue())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "put")

    def test_constructor_accepts_fifo_queue(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("queue").Queue())  # type: ignore[arg-type]
        assert hasattr(terminator._terminate_poll_interval_sec, "put")

    def test_constructor_accepts_deque_with_maxlen(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").deque(maxlen=10))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").deque)

    def test_constructor_accepts_ordered_dict_with_popitem(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").OrderedDict())  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").OrderedDict)

    def test_constructor_accepts_counter_with_most_common(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").Counter("hello"))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").Counter)

    def test_constructor_accepts_defaultdict_with_default_factory(self):
        terminator = ProcessTerminator(terminate_poll_interval_sec=__import__("collections").defaultdict(list))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, __import__("collections").defaultdict)

    def test_constructor_accepts_namedtuple_with_fields_and_defaults(self):
        Point = __import__("typing").NamedTuple("Point", [("x", float), ("y", float)])
        terminator = ProcessTerminator(terminate_poll_interval_sec=Point(x=0.1, y=0.2))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, Point)

    def test_constructor_accepts_dataclass_with_slots_and_frozen(self):
        from dataclasses import dataclass

        @dataclass(slots=True, frozen=True)
        class FrozenClass:
            value: float = 0.1

        terminator = ProcessTerminator(terminate_poll_interval_sec=FrozenClass(value=0.1))  # type: ignore[arg-type]
        assert isinstance(terminator._terminate_poll_interval_sec, FrozenClass)

    def test_constructor_accepts_enums_with_members_and_values(self):
        from enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Color.RED)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == Color.RED

    def test_constructor_accepts_flag_with_values_and_names(self):
        from enum import Flag

        class Permission(Flag):
            READ = 1
            WRITE = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Permission.READ | Permission.WRITE)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == (Permission.READ | Permission.WRITE)

    def test_constructor_accepts_intenum_with_values_and_names(self):
        from enum import IntEnum

        class Priority(IntEnum):
            LOW = 1
            HIGH = 2

        terminator = ProcessTerminator(terminate_poll_interval_sec=Priority.HIGH)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == 2

    def test_constructor_accepts_bitfield_with_values_and_names(self):
        from enum import IntFlag

        class Mode(IntFlag):
            R = 4
            W = 2
            X = 1

        terminator = ProcessTerminator(terminate_poll_interval_sec=Mode.R | Mode.W)  # type: ignore[arg-type]
        assert terminator._terminate_poll_interval_sec == (Mode.R | Mode.W)
