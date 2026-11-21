"""
Dashboard smoke test: renders every page in the navigation and drives every
selectbox, radio, slider and select-slider through its first, middle and last
value, failing on any exception. Snowflake is forced offline so the test never
uses the credentials in .env.
"""

import os
import re
import unittest

from streamlit.testing.v1 import AppTest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ["SNOWFLAKE_ACCOUNT"] = "your_snowflake_account_identifier"  # placeholder value = offline mode (load_dotenv won't override it)
PAGES = re.findall(r'P\("(pages/[^"]+)"', open(os.path.join(ROOT, "streamlit_app.py")).read())


def picks(values):
    values = list(values)
    return [values[i] for i in sorted({0, len(values) // 2, len(values) - 1})] if values else []


def drive(at, kind, set_fn, values_fn):
    """Sets each widget of one kind to a few values; returns the errors raised."""
    errors = []
    for i in range(len(getattr(at, kind))):
        if i >= len(getattr(at, kind)):  # a previous change removed widgets
            break
        for v in picks(values_fn(getattr(at, kind)[i])):
            set_fn(getattr(at, kind)[i], v)
            at.run()
            errors += [f"{kind}[{i}]={v!r}: {e.value}" for e in at.exception]
            if i >= len(getattr(at, kind)):
                break
    return errors


class TestDashboardPages(unittest.TestCase):

    def test_home_through_router(self):
        at = AppTest.from_file(os.path.join(ROOT, "streamlit_app.py"), default_timeout=180).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertIn("ApexIQ", " ".join(m.value for m in at.markdown))

    def test_every_page_and_widget(self):
        failures = {}
        for page in PAGES[1:]:  # home uses page links, covered by the router test
            at = AppTest.from_file(os.path.join(ROOT, page), default_timeout=180).run()
            errs = [f"render: {e.value}" for e in at.exception]
            if not errs:
                errs += drive(at, "selectbox", lambda w, v: w.select(v), lambda w: w.options)
                errs += drive(at, "radio", lambda w, v: w.set_value(v), lambda w: w.options)
                errs += drive(at, "select_slider", lambda w, v: w.set_value(v), lambda w: w.options)
                errs += drive(at, "slider", lambda w, v: w.set_value(v),
                              lambda w: [w.min, w.max] if not isinstance(w.value, tuple) else [(w.min, w.max)])
                errs += drive(at, "button", lambda w, v: w.click(), lambda w: [True])
            if errs:
                failures[page] = errs[:3]
        self.assertEqual(failures, {}, failures)


if __name__ == "__main__":
    unittest.main()
