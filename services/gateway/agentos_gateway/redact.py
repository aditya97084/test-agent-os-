"""Log redaction (Law 7): any env value that looks like a secret is scrubbed from every
log record, including stack texts. Applied at logging root handlers."""
from __future__ import annotations

import logging
import os

SECRETISH = ("KEY", "PASSWORD", "TOKEN", "SECRET", "DSN")
_MIN_LEN = 6


def _secret_values() -> set[str]:
    vals = set()
    for k, v in os.environ.items():
        if v and len(v) >= _MIN_LEN and any(s in k.upper() for s in SECRETISH):
            vals.add(v)
    return vals


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        vals = _secret_values()
        if vals:
            msg = record.getMessage()
            for v in vals:
                if v in msg:
                    msg = msg.replace(v, "***REDACTED***")
            record.msg, record.args = msg, ()
            if record.exc_text:
                t = record.exc_text
                for v in vals:
                    t = t.replace(v, "***REDACTED***")
                record.exc_text = t
        return True


def install_redaction() -> None:
    f = RedactFilter()
    root = logging.getLogger()
    for h in list(root.handlers):
        h.addFilter(f)
    if not root.handlers:
        h = logging.StreamHandler()
        h.addFilter(f)
        root.addHandler(h)
    root.addFilter(f)
