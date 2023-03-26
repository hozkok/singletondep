"""
Examples:
    # without shutdown
    @singleton_dependency
    def static_singleton_object(settings: pydantic.BaseSettings):
        return object()

    # without shutdown async
    @singleton_dependency
    async def async_singleton_object(settings: pydantic.BaseSettings):
        return await create_db(settings.db_url)

    # with async shutdown
    @singleton_dependency
    async def async_generator(settings: pydantic.BaseSettings):
        db = await create_db(settings.db_url)
        yield db
        await db.disconnect()

    # with sync shutdown
    @singleton_dependency
    def sync_generator_dependency(settings: pydantic.BaseSettings):
        sync_obj = create_sync_object()
        yield sync_obj
        sync_obj.shutdown()

    ...
    def setup_app():
        app = FastAPI()
        settings = Settings()
        for dep in singleton_deps:
            dep.register(app, settings)
        return app
"""

from enum import Enum
from typing import (
    Callable,
    AsyncGenerator,
    Generic,
    Literal,
    TypeAlias,
    Union,
    Any,
    Generator,
    ParamSpec,
    TypeVar,
    cast,
    overload,
    Awaitable,
)
from inspect import (
    isgeneratorfunction,
    iscoroutinefunction,
    isasyncgenfunction,
    isasyncgen,
)


# sentinel object for uninitialized dependency
class _Sentinel(Enum):
    UNINITIALIZED = "UNINITIALIZED"


UNINITIALIZED = _Sentinel.UNINITIALIZED

Uninitialized: TypeAlias = Literal[_Sentinel.UNINITIALIZED]
Params = ParamSpec("Params")
T = TypeVar("T")


class singleton_dependency(Generic[Params, T]):
    @overload
    def __init__(self, fn: Callable[Params, AsyncGenerator[T, None]]):
        ...

    @overload
    def __init__(self, fn: Callable[Params, Awaitable[T]]):
        ...

    @overload
    def __init__(self, fn: Callable[Params, Generator[T, None, None]]):
        ...

    @overload
    def __init__(self, fn: Callable[Params, T]):
        ...

    def __init__(self, fn: Callable[Params, Any]):
        self.fn = fn
        self._value: Uninitialized | T = UNINITIALIZED
        self._dirty_generator: Generator | AsyncGenerator | None = None

    def __call__(self) -> T:
        value = self._value
        if value is UNINITIALIZED:
            raise RuntimeError(f"dependency {self.fn} is not initialized")
        return value

    async def init(self, *args: Params.args, **kwargs: Params.kwargs):
        fn = self.fn
        if iscoroutinefunction(fn):
            value = await fn(*args, **kwargs)
        elif isasyncgenfunction(fn):
            async_gen = fn(*args, **kwargs)
            value = await async_gen.__anext__()
            self._dirty_generator = async_gen
        elif isgeneratorfunction(fn):
            gen = fn(*args, **kwargs)
            value = next(gen)
            self._dirty_generator = gen
        else:
            value = fn(*args, **kwargs)
        self._value = value

    async def cleanup(self):
        if self._dirty_generator is None:
            return
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
            raise RuntimeError("Make sure to have a single yield in singletonoid")

    def is_clean(self):
        """
        Returns True if dependency is not yet initialized or not require cleanup
        """
        return self._dirty_generator is None
