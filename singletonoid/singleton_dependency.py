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

from typing import (
    Callable,
    AsyncGenerator,
    Union,
    Any,
    Generator,
    ParamSpec,
)
from inspect import (
    isgeneratorfunction,
    iscoroutinefunction,
    isasyncgenfunction,
    isasyncgen,
)

from fastapi import FastAPI
from pydantic import BaseSettings


# sentinel object for uninitialized dependency
UNINITIALIZED = object()


class singleton_dependency:

    def __init__(self, fn: Callable[[BaseSettings], Any]):
        self.fn = fn
        self._value = UNINITIALIZED

    def __call__(self) -> Any:
        value = self._value
        if value is UNINITIALIZED:
            raise RuntimeError(f"dependency {self.fn} is not initialized")
        return value

    def register(self, app: FastAPI, settings: BaseSettings):
        cleanup = None

        @app.on_event("startup")
        async def _init_dependency():
            nonlocal cleanup
            fn = self.fn
            if iscoroutinefunction(fn):
                dep_value = await fn(settings)
            elif isasyncgenfunction(fn):
                gen = fn(settings)
                dep_value = await gen.__anext__()
                cleanup = _create_cleanup(gen)
            elif isgeneratorfunction(fn):
                gen = fn(settings)
                dep_value = next(gen)
                cleanup = _create_cleanup(gen)
            else:
                dep_value = fn(settings)
            self._value = dep_value

        @app.on_event("shutdown")
        async def _clear_dependency():
            if cleanup is not None:
                await cleanup()
            self._value = UNINITIALIZED


def _create_cleanup(
    gen: Union[AsyncGenerator, Generator],
) -> Callable[[], None]:
    if isasyncgen(gen):
        async def cleanup():
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                return
            else:
                raise RuntimeError("Did not cleanup dependency")
    else:
        async def cleanup():
            try:
                next(gen)
            except StopIteration:
                return
            else:
                raise RuntimeError("Did not cleanup dependency")
    return cleanup
