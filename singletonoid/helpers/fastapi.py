from typing import Any

from fastapi import FastAPI
from pydantic import BaseSettings

from singletonoid.errors import AlreadyCleanError
from singletonoid.singleton_dependency import singleton_dependency


def register_dep(
    dep: singleton_dependency[[BaseSettings], Any],
    app: FastAPI,
    settings: BaseSettings,
):
    @app.on_event("startup")
    async def _init_dep():
        await dep.init(settings)

    @app.on_event("shutdown")
    async def _clean_dep():
        try:
            await dep.cleanup()
        except AlreadyCleanError:
            pass
