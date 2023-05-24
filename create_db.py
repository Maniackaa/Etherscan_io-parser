import asyncio

from database.db import engine, init_models

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_models(engine))
    finally:
        loop.close()



