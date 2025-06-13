import unittest
from unittest.mock import MagicMock
import sys
from types import SimpleNamespace

# Provide a dummy crawl4ai module for tests
sys.modules.setdefault(
    "crawl4ai",
    SimpleNamespace(LLMExtractionStrategy=MagicMock(), LLMConfig=MagicMock()),
)

# Import the interpreter module directly to avoid importing full package deps
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "news_crawler.interpreters",
    str(Path(__file__).resolve().parent.parent / "news_crawler" / "interpreters.py"),
)
interpreter_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(interpreter_mod)
ArticleLinkInterpreter = interpreter_mod.ArticleLinkInterpreter


class TestArticleLinkInterpreter(unittest.TestCase):
    def setUp(self):
        # Bypass __init__ to avoid dependency on crawl4ai and pydantic v2
        self.interpreter = ArticleLinkInterpreter.__new__(ArticleLinkInterpreter)

    def test_find_recurrent_news_class(self):
        html = (
            "<html><body><main>"
            "<div class='news-item'>A</div>"
            "<div class='news-item'>B</div>"
            "<div class='other'>C</div>"
            "</main></body></html>"
        )
        cls = self.interpreter.find_recurrent_news_class(html)
        self.assertEqual(cls, "news-item")

    def test_find_recurrent_news_class_none(self):
        html = "<html><body><main><div class='unique'>X</div></main></body></html>"
        cls = self.interpreter.find_recurrent_news_class(html)
        self.assertIsNone(cls)


if __name__ == "__main__":
    unittest.main()
