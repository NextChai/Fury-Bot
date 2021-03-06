"""
Mozilla Public License Version 2
================================

Copyright (c) 2016-present Rapptz

Full copyright can be found here: https://github.com/Rapptz/RoboDanny/blob/rewrite/LICENSE.txt
"""

from __future__ import annotations

import re
import datetime
from dateutil.relativedelta import relativedelta
import parsedatetime as pdt
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Type, TypeVar, Union

from discord.ext import commands

if TYPE_CHECKING:
    from .context import Context

__all__: Tuple[str, ...] = (
    'ShortTime',
    'HumanTime',
    'Time',
    'FutureTime',
    'UserFriendlyTime',
    'plural',
    'human_join',
    'human_timedelta',
)

STT = TypeVar('STT', bound='ShortTime')
HTT = TypeVar('HTT', bound='HumanTime')
TT = TypeVar('TT', bound='Time')

# Monkey patch mins and secs into the units
units = pdt.pdtLocales['en_US'].units
units['minutes'].append('mins')
units['seconds'].append('secs')


class ShortTime:
    __slots__: Tuple[str, ...] = ('dt',)

    compiled = re.compile(
        """(?:(?P<years>[0-9])(?:years?|y))?             # e.g. 2y
                             (?:(?P<months>[0-9]{1,2})(?:months?|mo))?     # e.g. 2months
                             (?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?        # e.g. 10w
                             (?:(?P<days>[0-9]{1,5})(?:days?|d))?          # e.g. 14d
                             (?:(?P<hours>[0-9]{1,5})(?:hours?|h))?        # e.g. 12h
                             (?:(?P<minutes>[0-9]{1,5})(?:minutes?|m))?    # e.g. 10m
                             (?:(?P<seconds>[0-9]{1,5})(?:seconds?|s))?    # e.g. 15s
                          """,
        re.VERBOSE,
    )

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None) -> None:
        match = self.compiled.fullmatch(argument)
        if match is None or not match.group(0):
            raise commands.BadArgument('invalid time provided')

        data = {k: int(v) for k, v in match.groupdict(default=0).items()}
        now = now or datetime.datetime.now(datetime.timezone.utc)
        self.dt = now + relativedelta(**data)

    @classmethod
    async def convert(cls: Type[STT], ctx: Context, argument: str) -> STT:
        now = ctx.message.created_at
        return cls(argument, now=now)


class HumanTime:
    __slots__: Tuple[str, ...] = ('dt', '_past')

    calendar = pdt.Calendar(version=pdt.VERSION_CONTEXT_STYLE)

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None) -> None:
        now = now or datetime.datetime.utcnow()
        dt, status = self.calendar.parseDT(argument, sourceTime=now)
        if not status.hasDateOrTime:
            raise commands.BadArgument('invalid time provided, try e.g. "tomorrow" or "3 days"')

        if not status.hasTime:
            # replace it with the current time
            dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

        self.dt = dt
        self._past = dt < now

    @classmethod
    async def convert(cls: Type[HTT], ctx: Context, argument: str) -> HTT:
        now = ctx.message.created_at
        return cls(argument, now=now)


class Time(HumanTime):
    __slots__: Tuple[str, ...] = ()

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None) -> None:
        try:
            o = ShortTime(argument, now=now)
        except Exception as e:
            super().__init__(argument)
        else:
            self.dt = o.dt
            self._past = False


class FutureTime(Time):
    __slots__: Tuple[str, ...] = ()

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None) -> None:
        super().__init__(argument, now=now)

        if self._past:
            raise commands.BadArgument('this time is in the past')


class UserFriendlyTime(commands.Converter):
    """That way quotes aren't absolutely necessary."""

    if TYPE_CHECKING:
        arg: str

    __slots__: Tuple[str, ...] = (
        'converter',
        'dt',
        'arg',
        'default',
    )

    def __init__(
        self,
        converter: Optional[Union[Callable[[Context, str], Any], Type[commands.Converter], commands.Converter]] = None,
        *,
        default: Optional[str] = None,
        force_future: bool = True,
    ) -> None:
        if isinstance(converter, type) and issubclass(converter, commands.Converter):
            converter = converter()  # type: ignore

        if converter is not None and not isinstance(converter, commands.Converter):
            raise TypeError('commands.Converter subclass necessary.')

        self.converter: Optional[
            Union[Callable[[Context, str], Any], Type[commands.Converter], commands.Converter]
        ] = converter

        self.default: Optional[str] = default
        self.force_future: bool = force_future

    async def check_constraints(self, ctx: Context, now: datetime.datetime, remaining: str) -> UserFriendlyTime:
        if self.force_future and self.dt < now:
            raise commands.BadArgument('This time is in the past.')

        if not remaining:
            if self.default is None:
                raise commands.BadArgument('Missing argument after the time.')
            remaining = self.default

        if self.converter is not None:
            self.arg = await self.converter.convert(ctx, remaining)  # type: ignore
        else:
            self.arg = remaining

        return self

    def copy(self) -> UserFriendlyTime:
        cls = self.__class__
        obj = cls.__new__(cls)
        obj.converter = self.converter
        obj.default = self.default
        obj.force_future = self.force_future
        return obj

    async def convert(self, ctx: Context, argument: str) -> UserFriendlyTime:
        # Create a copy of ourselves to prevent race conditions from two
        # events modifying the same instance of a converter
        result = self.copy()
        try:
            calendar = HumanTime.calendar
            regex = ShortTime.compiled

            now = ctx.message.created_at

            match = regex.match(argument)
            if match is not None and match.group(0):
                data = {k: int(v) for k, v in match.groupdict(default=0).items()}
                remaining = argument[match.end() :].strip()
                result.dt = now + relativedelta(**data)
                return await result.check_constraints(ctx, now, remaining)

            # apparently nlp does not like "from now"
            # it likes "from x" in other cases though so let me handle the 'now' case
            if argument.endswith('from now'):
                argument = argument[:-8].strip()

            if argument[0:2] == 'me':
                # starts with "me to", "me in", or "me at "
                if argument[0:6] in ('me to ', 'me in ', 'me at '):
                    argument = argument[6:]

            elements = calendar.nlp(argument, sourceTime=now)
            if elements is None or len(elements) == 0:
                raise commands.BadArgument('Invalid time provided, try e.g. "tomorrow" or "3 days".')

            # handle the following cases:
            # "date time" foo
            # date time foo
            # foo date time

            # first the first two cases:
            dt, status, begin, end, dt_string = elements[0]

            if not status.hasDateOrTime:
                raise commands.BadArgument('Invalid time provided, try e.g. "tomorrow" or "3 days".')

            if begin not in (0, 1) and end != len(argument):
                raise commands.BadArgument(
                    'Time is either in an inappropriate location, which '
                    'must be either at the end or beginning of your input, '
                    'or I just flat out did not understand what you meant. Sorry.'
                )

            if not status.hasTime:
                # replace it with the current time
                dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

            # if midnight is provided, just default to next day
            if status.accuracy == pdt.pdtContext.ACU_HALFDAY:
                dt = dt.replace(day=now.day + 1)

            result.dt = dt.replace(tzinfo=datetime.timezone.utc)

            if begin in (0, 1):
                if begin == 1:
                    # check if it's quoted:
                    if argument[0] != '"':
                        raise commands.BadArgument('Expected quote before time input...')

                    if not (end < len(argument) and argument[end] == '"'):
                        raise commands.BadArgument('If the time is quoted, you must unquote it.')

                    remaining = argument[end + 1 :].lstrip(' ,.!')
                else:
                    remaining = argument[end:].lstrip(' ,.!')
            elif len(argument) == end:
                remaining = argument[:begin].strip()

            return await result.check_constraints(ctx, now, remaining)  # type: ignore
        except:
            import traceback

            traceback.print_exc()
            raise


class plural:
    def __init__(self, value: int) -> None:
        self.value: int = value

    def __format__(self, format_spec: str) -> str:
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'

        if abs(v) != 1:
            return f'{v} {plural}'

        return f'{v} {singular}'


def human_join(seq: List[str], delim=', ', final='or') -> str:
    size = len(seq)
    if size == 0:
        return ''

    if size == 1:
        return seq[0]

    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'

    return delim.join(seq[:-1]) + f' {final} {seq[-1]}'


def human_timedelta(
    dt: datetime.datetime,
    *,
    source: Optional[datetime.datetime] = None,
    accuracy: int = 3,
    brief: bool = False,
    suffix: Union[bool, str] = True,
) -> str:
    now = source or datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)

    # Microsecond free zone
    now = now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)

    # This implementation uses relativedelta instead of the much more obvious
    # divmod approach with seconds because the seconds approach is not entirely
    # accurate once you go over 1 week in terms of accuracy since you have to
    # hardcode a month as 30 or 31 days.
    # A query like "11 months" can be interpreted as "!1 months and 6 days"
    if dt > now:
        delta = relativedelta(dt, now)
        suffix = ''
    else:
        delta = relativedelta(now, dt)
        suffix = ' ago' if suffix else ''

    attrs = [
        ('year', 'y'),
        ('month', 'mo'),
        ('day', 'd'),
        ('hour', 'h'),
        ('minute', 'm'),
        ('second', 's'),
    ]

    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + 's')
        if not elem:
            continue

        if attr == 'day':
            weeks = delta.weeks
            if weeks:
                elem -= weeks * 7
                if not brief:
                    output.append(format(plural(weeks), 'week'))
                else:
                    output.append(f'{weeks}w')

        if elem <= 0:
            continue

        if brief:
            output.append(f'{elem}{brief_attr}')
        else:
            output.append(format(plural(elem), attr))

    if accuracy is not None:
        output = output[:accuracy]

    if len(output) == 0:
        return 'now'
    else:
        if not brief:
            return human_join(output, final='and') + suffix
        else:
            return ' '.join(output) + suffix


def td_format(td_object: datetime.timedelta) -> str:
    seconds = int(td_object.total_seconds())
    periods: List[Tuple[str, float]] = [
        ('year', 60 * 60 * 24 * 365),
        ('month', 60 * 60 * 24 * 30),
        ('day', 60 * 60 * 24),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1),
        ('millisecond', 1 / 1000),
        ('microsecond', 1 / 1e6),
    ]

    strings: List[str] = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return human_join(strings, final='and')
