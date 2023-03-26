Singletonoid
----------------------------

Fully typed dependency management library focusing simplicity and flexibility.

### Requirements

python >= 3.11

### Installation

```sh
pip install singletonoid
```

### Usage

```python
from singletonoid import singleton_dependency

@singleton_dependency
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


This library is especially useful for managing singletons in large projects.
