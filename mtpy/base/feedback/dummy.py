"""Dummy feedback modules for testing and silencing feedback."""

from typing import IO, Any, Generic, Iterable, Iterator, Mapping, TypeVar

T_co = TypeVar("T_co", covariant=True)


class DummyLogger:
    """A dummy object placeholding for logger objects accepted by MTPy classes."""

    def debug(self: "DummyLogger", message: str, *args: Any, **kwargs: Any) -> None:
        """Emits a debug level log message.

        Args:
            message (str): The message to be emitted
            *args (Any): The extra args to be passed to the emitter
            **kwargs (Any): The extra kwargs to be passed to the emitter
        """
        pass

    def info(self: "DummyLogger", message: str, *args: Any, **kwargs: Any) -> None:
        """Emits an info level log message.

        Args:
            message (str): The message to be emitted
            *args (Any): The extra args to be passed to the emitter
            **kwargs (Any): The extra kwargs to be passed to the emitter
        """
        pass

    def warning(self: "DummyLogger", message: str, *args: Any, **kwargs: Any) -> None:
        """Emits a warning level log message.

        Args:
            message (str): The message to be emitted
            *args (Any): The extra args to be passed to the emitter
            **kwargs (Any): The extra kwargs to be passed to the emitter
        """
        pass

    def error(self: "DummyLogger", message: str, *args: Any, **kwargs: Any) -> None:
        """Emits an error level log message.

        Args:
            message (str): The message to be emitted
            *args (Any): The extra args to be passed to the emitter
            **kwargs (Any): The extra kwargs to be passed to the emitter
        """
        pass

    def critical(self: "DummyLogger", message: str, *args: Any, **kwargs: Any) -> None:
        """Emits a critical level log message.

        Args:
            message (str): The message to be emitted
            *args (Any): The extra args to be passed to the emitter
            **kwargs (Any): The extra kwargs to be passed to the emitter
        """
        pass


class DummyProgressBar(Generic[T_co]):
    """Initialiser for creating progress bars.

    I really like how tqdm handles progress bars, so as a start lets enforce
    an identical interface. Documentation has been duplicated from `tqdm.__init__`

    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.

    Args:
        iterable (Iterable[T_co] | None): Iterable to decorate with a progressbar.
            Leave blank to manually manage the updates.
        *args (Any): Additional args to be accepted depending on implementation
        desc (str | None): Prefix for the progressbar.
        total (float | None): The number of expected iterations. If unspecified,
            len(iterable) is used if possible. If float("inf") or as a last
            resort, only basic progress statistics are displayed
            (no ETA, no progressbar).
            If `gui` is True and this parameter needs subsequent updating,
            specify an initial arbitrary large positive number,
            e.g. 9e9.
        leave (bool | None): If [default: True], keeps all traces of the progressbar
            upon termination of iteration.
            If `None`, will leave only if `position` is `0`.
        file (IO[str] | None): Specifies where to output the progress messages
            (default: sys.stderr). Uses `file.write(str)` and `file.flush()`
            methods.  For encoding, see `write_bytes`.
        ncols (int | None): The width of the entire output message. If specified,
            dynamically resizes the progressbar to stay within this bound.
            If unspecified, attempts to use environment width. The
            fallback is a meter width of 10 and no limit for the counter and
            statistics. If 0, will not print any meter (only stats).
        mininterval (float): Minimum progress display update interval [default: 0.1] seconds.
        maxinterval (float): Maximum progress display update interval [default: 10] seconds.
            Automatically adjusts `miniters` to correspond to `mininterval`
            after long display update lag. Only works if `dynamic_miniters`
            or monitor thread is enabled.
        miniters (float | None): Minimum progress display update interval, in iterations.
            If 0 and `dynamic_miniters`, will automatically adjust to equal
            `mininterval` (more CPU efficient, good for tight loops).
            If > 0, will skip display of specified number of iterations.
            Tweak this and `mininterval` to get very efficient loops.
            If your progress is erratic with both fast and slow iterations
            (network, skipping items, etc) you should set miniters=1.
        ascii (bool | str | None): If unspecified or False, use unicode (smooth blocks) to fill
            the meter. The fallback is to use ASCII characters " 123456789#".
        disable (bool | None): Whether to disable the entire progressbar wrapper
            [default: False]. If set to None, disable on non-TTY.
        unit (str): String that will be used to define the unit of each iteration
            [default: it].
        unit_scale (bool | float): If 1 or True, the number of iterations will be reduced/scaled
            automatically and a metric prefix following the
            International System of Units standard will be added
            (kilo, mega, etc.) [default: False]. If any other non-zero
            number, will scale `total` and `n`.
        dynamic_ncols (bool): If set, constantly alters `ncols` and `nrows` to the
            environment (allowing for window resizes) [default: False].
        smoothing (float): Exponential moving average smoothing factor for speed estimates
            (ignored in GUI mode). Ranges from 0 (average speed) to 1
            (current/instantaneous speed) [default: 0.3].
        bar_format (str | None): Specify a custom bar string formatting. May impact performance.
            [default: '{l_bar}{bar}{r_bar}'], where
            l_bar='{desc}: {percentage:3.0f}%|' and
            r_bar='| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, '
                '{rate_fmt}{postfix}]'
            Possible vars: l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
                percentage, elapsed, elapsed_s, ncols, nrows, desc, unit,
                rate, rate_fmt, rate_noinv, rate_noinv_fmt,
                rate_inv, rate_inv_fmt, postfix, unit_divisor,
                remaining, remaining_s, eta.
            Note that a trailing ": " is automatically removed after {desc}
            if the latter is empty.
        initial (float): The initial counter value. Useful when restarting a progress
            bar [default:.3f}`
            or similar in `bar_format`, or specifying `unit_scale`.
        position (int | None): Specify the line offset to print this bar (starting from 0)
            Automatic if unspecified.
            Useful to manage multiple bars at once (eg, from threads).
        postfix (Mapping[str, object] | str | None): Specify additional stats to display at the
            end of the bar. Calls `set_postfix(**postfix)` if possible (dict).
        unit_divisor (float): [default: 1000], ignored unless `unit_scale` is True.
        write_bytes (bool): Whether to write bytes. If (default: False) will write unicode.
        lock_args (tuple[bool | None, float | None] | tuple[bool | None] | None):
            Passed to `refresh` for intermediate output
            (initialisation, iterating, and updating).
        nrows (int | None): The screen height. If specified, hides nested bars outside this
            bound. If unspecified, attempts to use environment height.
            The fallback is 20.
        colour (str | None): Bar colour (e.g. 'green', '#00ff00').
        delay (float | None): Don't display until [default: 0] seconds have elapsed.
        gui (bool): WARNING: internal parameter - do not use.
            Use tqdm.gui.tqdm(...) instead. If set, will attempt to use
            matplotlib animations for a graphical output [default: False].
        **kwargs (Any): Additional kwargs to be passed based on implementation.

    Attributes:
        iterable (Iterable[T_co] | None): The iterator to wrap.
    """

    iterable: Iterable[T_co] | None

    # NOTE: Ignoring some of the warnings here as this is not a protocol i
    #     I've defined myself. It's not getting fixed here unless TQDM fixes
    #     it or we change protocol.
    def __init__(
        self: "DummyProgressBar[T_co]",
        iterable: Iterable[T_co] | None = None,
        *args: Any,
        desc: str | None = None,
        total: float | None = None,
        leave: bool | None = None,
        file: IO[str] | None = None,
        ncols: int | None = None,
        mininterval: float = 0.1,
        maxinterval: float = 10,
        miniters: float | None = 0,
        ascii: bool | str | None = None,  # noqa A002
        disable: bool | None = False,
        unit: str = "it",
        unit_scale: bool | float = False,
        dynamic_ncols: bool = False,  # FBT001
        smoothing: float = 0.3,
        bar_format: str | None = None,
        initial: float = 0.0,
        position: int | None = None,
        postfix: Mapping[str, object] | str | None = None,
        unit_divisor: float = 1000.0,
        write_bytes: bool = False,  # FBT001
        lock_args: tuple[bool | None, float | None] | tuple[bool | None] | None = None,
        nrows: int | None = None,
        colour: str | None = None,
        delay: float | None = None,
        gui: bool = False,  # FBT001
        **kwargs: Any,
    ) -> None:
        self.iterable = iterable

    def __iter__(self: "DummyProgressBar[T_co]") -> Iterator[T_co]:
        """Backward-compatibility to use: for x in tqdm(iterable).

        Returns:
            Iterator[T_co]: An the wrapped iterator.
        """
        return self.iterable.__iter__() if self.iterable is not None else ().__iter__()

    def update(self: "DummyProgressBar[T_co]", n: int | float = 1) -> bool | None:
        """Manually update the progress bar, useful for streams such as reading files.

        E.g.:
        >>> t = tqdm(total=filesize) # Initialise
        >>> for current_buffer in stream:
        ...    ...
        ...    t.update(len(current_buffer))
        >>> t.close()
        The last line is highly recommended, but possibly not necessary if
        `t.update()` will be called in such a way that `filesize` will be
        exactly reached and printed.

        Args:
            n (int | float, optional): Increment to add to the internal
                counter of iterations [default: 1]. If using float, consider
                specifying `{n:.3f}` or similar in `bar_format`, or specifying
                `unit_scale`.

        Returns:
            bool | None: True if a `display()` was triggered.
        """
        return None
