singletondep
------------

Fully typed dependency management library focusing simplicity and flexibility.

## Motivation

This library aims to provide a simple approach to singleton dependency
management in projects. In modern live systems, there can be many objects that
are expensive and hard to control background tasks, connections, pools
life-cycles.

Frameworks either have a very opinionated view on this, or rely on module-level
defined objects which may require dynamic parameters that are injected during
application startup. This causes module structures to access global variables
or importing completely unrelated modules in order to manage singleton
dependencies lifecycles applying anti-patterns all around.

This library provides a simple approach to this problem by using simple
abstraction over raw functions.

## Requirements

python >= 3.10

### Installation

```sh
pip install singletondep
```

### Usage

```python
from singletondep import singletondep

@singletondep
async def get_db(db_url: str):
    db = Database(settings.db_url)
    await db.connect()
    print("connection established")
    yield db
    await db.disconnect()
    print("disconnected from db")


async def main():
    db_url = "localhost/db_name"
    await get_db.init(db_url)
    # out: connection established
    db = get_db()
    ...
    await get_db.cleanup()
    # out: disconnected from db
```

This library can be especially useful to manage dependencies in larger projects.


### Using as a FastAPI Dependency

```python
import os

from fastapi import FastAPI, APIRouter, Depends
from pydantic import BaseSettings
from singletondep import singletondep
from singletondep.ext.fastapi import register_dep


class Settings(BaseSettings):
    url: str


@singletondep
async def get_db(settings: Settings):
    db = await create_connection(settings.url)
    print("connected to db")
    yield db
    await db.disconnect()
    print("closed db connections")


router = APIRouter()

@router.get("/meaning")
async def get_meaning(db = Depends(get_db)):
    meaning = await db.fetch_meaning()
    return f"the meaning is {meaning}"


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    settings = Settings(url=os.environ["url"])
    register_dep(get_db, app, settings)
    return app
```
