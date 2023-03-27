from typing import Any

from fastapi import FastAPI
from pydantic import BaseSettings

from singletondep.errors import AlreadyCleanError
from singletondep.singletondep import singletondep


def register_dep(
    dep: singletondep[[BaseSettings], Any],
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
