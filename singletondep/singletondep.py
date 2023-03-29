"""
Provides fully typed @singletondep decorator for once off dependencies
life-cycle management.
"""
from enum import Enum
from inspect import (
    isasyncgen,
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
)
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Literal,
    ParamSpec,
    TypeAlias,
    TypeVar,
    cast,
)

from singletondep.errors import (
    AlreadyCleanError,
    AlreadyInitializedError,
    NotInitializedError,
)


# sentinel object for uninitialized dependency
class _Sentinel(Enum):
    UNINITIALIZED = "UNINITIALIZED"


UNINITIALIZED = _Sentinel.UNINITIALIZED

Uninitialized: TypeAlias = Literal[_Sentinel.UNINITIALIZED]
Params = ParamSpec("Params")
T = TypeVar("T")


class singletondep(Generic[Params, T]):
    """
    Decorator for managing singleton dependency life-cycles.
    Supports:
        - normal functions
        - coroutine functions
        - generator functions
        - async generator functions
    Examples:
        >>> @singletondep
        >>> async def get_db(db_url: str):
        >>>     db = await create_db(db_url)
        >>>     yield db
        >>>     await db.disconnect()

        >>> async main():
        >>>     await get_db.init("postgres://db_url")
        >>>     db = get_db()  # returns the yielded db object
        >>>     await get_db.cleanup()  # cleans up the connection
        >>>     db = get_db()  # raises NotInitializedError
    """

    def __init__(
        self,
        fn: Callable[
            Params,
            AsyncGenerator[T, None]
            | Awaitable[T]
            | Generator[T, None, None]
            | T,
        ],
    ):
        self.fn = fn
        self._value: Uninitialized | T = UNINITIALIZED
        self._dirty_generator: (
            Generator[T, None, None] | AsyncGenerator[T, None] | None
        ) = None

    def __call__(self) -> T:
        value = self._value
        if value is UNINITIALIZED:
            raise NotInitializedError(
                f"dependency {self.fn} is not initialized"
            )
        return value

    async def init(self, *args: Params.args, **kwargs: Params.kwargs):
        """
        Initializes the :class:`singletondep` object. This should be called
        only once. Raises :class:`AlreadyInitializedError` if called multiple
        times without `cleanup`.
        """
        if self._value is not UNINITIALIZED:
            raise AlreadyInitializedError("dependency is already initialized")
        fn = self.fn
        if iscoroutinefunction(fn):
            fn = cast(Callable[Params, Awaitable[T]], fn)
            value = await fn(*args, **kwargs)
        elif isasyncgenfunction(fn):
            fn = cast(Callable[Params, AsyncGenerator[T, None]], fn)
            async_gen = fn(*args, **kwargs)
            value = await async_gen.__anext__()
            self._dirty_generator = async_gen
        elif isgeneratorfunction(fn):
            fn = cast(Callable[Params, Generator[T, None, None]], fn)
            gen = fn(*args, **kwargs)
            value = next(gen)
            self._dirty_generator = gen
        else:
            fn = cast(Callable[Params, T], fn)
            value = fn(*args, **kwargs)
        self._value = value

    async def cleanup(self):
        """
        Cleans the dependency by running the code after yielded value. Only
        applicable for `Generator` and `AsyncGenerator` types of dependencies
        that are initialized by `init` method. Otherwise raises
        `AlreadyCleanError` error.
        """
        if self._dirty_generator is None:
            raise AlreadyCleanError()
        gen = self._dirty_generator
        try:
            if isasyncgen(gen):
                gen = cast(AsyncGenerator, gen)
                await gen.__anext__()
            else:
                gen = cast(Generator, gen)
                next(gen)
        except (StopIteration, StopAsyncIteration):
            return
        else:
            raise TypeError("Make sure to have a single yield in dependency")
        finally:
            self._value = UNINITIALIZED
            self._dirty_generator = None

    def is_clean(self):
        """
        Returns True if dependency does not require `cleanup()`
        """
        return self._dirty_generator is None
