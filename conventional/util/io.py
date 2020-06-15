import asyncio
import datetime

import dateutil


class AsyncFileObject:
    def __init__(self, f):
        self.f = f

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__enter__)

    async def __aexit__(self, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.f.__exit__, *args)


def json_defaults(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.astimezone(dateutil.tz.UTC).isoformat()

    raise TypeError("Type %s not serializable" % type(obj))
