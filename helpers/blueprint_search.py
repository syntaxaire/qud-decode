import asyncio
import concurrent.futures

from fuzzywuzzy import process

from shared import qindex


def find_exact_blueprint(query: str):
    """Return the matching blueprint, or None."""
    obj = None
    for key, val in qindex.items():
        if query.lower() == key.lower():
            obj = val
            break
    return obj


async def find_closest_blueprint(query: str):
    """Return the name of the closest blueprint match to the query."""
    loop = asyncio.get_running_loop()
    # doing a fuzzy match on the qindex keys can take about 2 seconds, so
    # run in an executor so we can keep processing other commands in the meantime
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool,
                                          process.extractOne,
                                          query,
                                          list(qindex))
