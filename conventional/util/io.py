import datetime
from typing import Any

import dateutil.tz


def json_defaults(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime.datetime):
        return obj.astimezone(dateutil.tz.UTC).isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()

    raise TypeError("Type %s not serializable" % type(obj))
