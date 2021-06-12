FastAPI Singleton Dependency
----------------------------

### Requirements

python >= 3.8

### Installation

```sh
pip install fastapi_singleton
```

### Usage

from fastapi import FastAPI
from pydantic import BaseSettings
from fastapi_singleton import singleton_dependency


```python

class Settings(BaseSettings):
    db_url: str
    
    
@singleton_dependency
async def get_db(settings: Settings):
    db = Database(settings.db_url)
    await db.connect()
    yield db
    await db.disconnect()
    

...


def create_app():
    settings = Settings()
    app = FastAPI()
    
    @app.get("/path")
    def handle_path(db=Depends(get_db)):
        data = await db.get_data()
        return data
    
    get_db.register(app, settings)
```
