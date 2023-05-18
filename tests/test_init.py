import os
from datetime import datetime, timedelta

import opensafely


def test_should_version_check():
    opensafely.VERSION_FILE.unlink(missing_ok=True)

    assert opensafely.should_version_check() is True
    opensafely.update_version_check()
    assert opensafely.should_version_check() is False

    timestamp = (datetime.utcnow() - timedelta(hours=5)).timestamp()
    os.utime(opensafely.VERSION_FILE, (timestamp, timestamp))

    assert opensafely.should_version_check() is True
