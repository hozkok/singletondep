import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseSettings

from singletondep import singletondep
from singletondep.helpers.fastapi import register_dep

DEPENDENCY_VALUE = "DEPENDENCY_VALUE"


@pytest.fixture(scope="module")
def settings():
    class Settings(BaseSettings):
        s1: str
        s2: str
    return Settings(s1="testsetting1", s2="testsetting2")


@pytest.fixture
def app():
    return FastAPI()


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def ctx():
    return {
        "call_count": 0,
        "cleanup": False,
        "settings": None,
    }


@pytest.fixture
def func_dep(ctx):
    def dep_fn(settings):
        ctx["call_count"] += 1
        ctx["settings"] = settings
        return DEPENDENCY_VALUE
    return dep_fn


@pytest.fixture
def coro_dep(ctx):
    async def dep_fn(settings):
        ctx["call_count"] += 1
        ctx["settings"] = settings
        return DEPENDENCY_VALUE
    return dep_fn


@pytest.fixture
def generator_dep(ctx):
    def dep_fn(settings):
        ctx["call_count"] += 1
        ctx["settings"] = settings
        yield DEPENDENCY_VALUE
        ctx["cleanup"] = True
    return dep_fn


@pytest.fixture
def async_generator_dep(ctx):
    async def dep_fn(settings):
        ctx["call_count"] += 1
        ctx["settings"] = settings
        yield DEPENDENCY_VALUE
        ctx["cleanup"] = True
    return dep_fn


@pytest.fixture
def dep(app, settings, request):

    dep = request.getfixturevalue(request.param)
    dep = singletondep(dep)

    @app.get("/test")
    def handle_test(d=Depends(dep)):
        return d

    register_dep(dep, app, settings)

    return dep


@pytest.mark.parametrize("dep", ["func_dep", "coro_dep"], indirect=True)
def test_dep(app, dep, settings, ctx):
    with TestClient(app) as client:
        resp = client.get("/test")
        resp = client.get("/test")
        assert resp.json() == DEPENDENCY_VALUE
        assert ctx["call_count"] == 1
        assert ctx["settings"] is settings


@pytest.mark.parametrize("dep", ["generator_dep", "async_generator_dep"], indirect=True)
def test_gen_dep(app, dep, settings, ctx):
    with TestClient(app) as client:
        resp = client.get("/test")
        resp = client.get("/test")
        assert resp.json() == DEPENDENCY_VALUE
        assert ctx["call_count"] == 1
        assert ctx["settings"] is settings
        assert ctx["cleanup"] is False
    assert ctx["cleanup"] is True
