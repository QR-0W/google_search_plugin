from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import importlib
import sys
import types
import unittest


PLUGIN_DIR = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "search_plugin_tool_tests"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PLUGIN_DIR)]
sys.modules[PACKAGE_NAME] = package
plugin_module = importlib.import_module(f"{PACKAGE_NAME}.plugin")
config_module = importlib.import_module(f"{PACKAGE_NAME}.config")
GoogleSearchPlugin = plugin_module.GoogleSearchPlugin


class ToolBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_keyword_search_keeps_topic_and_aliases(self):
        pipeline = SimpleNamespace(run=AsyncMock(return_value="search result"))
        url_pipeline = SimpleNamespace(run=AsyncMock())
        target = SimpleNamespace(
            _ensure_pipelines_ready=Mock(return_value=True),
            _resolve_bot_name=AsyncMock(return_value="fixture"),
            _search_pipeline=pipeline,
            _url_pipeline=url_pipeline,
            ctx=SimpleNamespace(logger=Mock()),
        )
        result = await GoogleSearchPlugin.handle_web_search(target, query="山雀 万能青年旅店", tavily_topic=" NEWS ")
        self.assertEqual(result, {"name": "web_search", "content": "search result"})
        pipeline.run.assert_awaited_once_with("山雀 万能青年旅店", bot_name="fixture", tavily_topic_override="news")
        url_pipeline.run.assert_not_awaited()

    async def test_search_rejects_url_before_initializing(self):
        for alias in ("question", "query", "q", "search_query", "keyword"):
            with self.subTest(alias=alias):
                result = await GoogleSearchPlugin.handle_web_search(SimpleNamespace(), **{alias: " https://example.org/page "})
                self.assertEqual(result["name"], "web_search")
                self.assertIn("不接受单独的网页链接", result["content"])

    async def test_disabled_summary_never_initializes_or_calls_models(self):
        target = SimpleNamespace(config=SimpleNamespace(search_backend=SimpleNamespace(summarize_webpage_enabled=False)))
        result = await GoogleSearchPlugin.handle_summarize_webpage(target, url="https://example.org/page")
        self.assertEqual(result, {"name": "summarize_webpage", "content": "网页总结工具已关闭。"})

    async def test_summary_rejects_non_url(self):
        target = SimpleNamespace(config=SimpleNamespace(search_backend=SimpleNamespace(summarize_webpage_enabled=True)))
        for value in ("", "search words", "ftp://example.org/file"):
            with self.subTest(value=value):
                result = await GoogleSearchPlugin.handle_summarize_webpage(target, url=value)
                self.assertIn("完整的 HTTP(S)", result["content"])

    async def test_enabled_summary_uses_only_url_pipeline(self):
        url_pipeline = SimpleNamespace(run=AsyncMock(return_value="page summary"))
        search_pipeline = SimpleNamespace(run=AsyncMock())
        target = SimpleNamespace(
            config=SimpleNamespace(search_backend=SimpleNamespace(summarize_webpage_enabled=True)),
            _ensure_pipelines_ready=Mock(return_value=True),
            _resolve_bot_name=AsyncMock(return_value="fixture"),
            _url_pipeline=url_pipeline,
            _search_pipeline=search_pipeline,
            ctx=SimpleNamespace(logger=Mock()),
        )
        result = await GoogleSearchPlugin.handle_summarize_webpage(target, url=" https://example.org/page ")
        self.assertEqual(result, {"name": "summarize_webpage", "content": "page summary"})
        url_pipeline.run.assert_awaited_once_with("https://example.org/page", bot_name="fixture")
        search_pipeline.run.assert_not_awaited()

    def test_both_tools_registered_summary_disabled_by_default(self):
        components = {c["name"]: c for c in plugin_module.create_plugin().get_components()}
        self.assertIn("web_search", components)
        self.assertFalse(components["summarize_webpage"]["metadata"]["enabled"])
        self.assertEqual(components["summarize_webpage"]["metadata"]["timeout_ms"], components["web_search"]["metadata"]["timeout_ms"])
        self.assertTrue({"abbreviation_translate", "image_search", "google_search_status"} <= components.keys())

    def test_legacy_configuration_defaults_summary_to_disabled(self):
        cfg = config_module.GoogleSearchPluginConfig.model_validate({"plugin": {"config_version": "4.0.0"}})
        self.assertFalse(cfg.search_backend.summarize_webpage_enabled)
        self.assertTrue(cfg.search_backend.fetch_content)

    async def test_summary_switch_controls_registration_and_hot_updates(self):
        plugin = plugin_module.create_plugin()
        enable = AsyncMock(return_value={"success": True})
        disable = AsyncMock(return_value={"success": True})
        context = SimpleNamespace(component=SimpleNamespace(enable_component=enable, disable_component=disable), logger=Mock())
        for enabled in (True, False):
            cfg = config_module.GoogleSearchPluginConfig()
            cfg.search_backend.summarize_webpage_enabled = enabled
            with patch.object(GoogleSearchPlugin, "config", new_callable=PropertyMock, return_value=cfg), patch.object(GoogleSearchPlugin, "ctx", new_callable=PropertyMock, return_value=context):
                entries = {c["name"]: c for c in plugin.get_components()}
                self.assertEqual(entries["summarize_webpage"]["metadata"]["enabled"], enabled)
                await plugin._sync_component_states()
        enable.assert_any_await("summarize_webpage", "tool")
        disable.assert_any_await("summarize_webpage", "tool")

    def test_summary_switch_visible_without_duplicate_bindings(self):
        schema = plugin_module.create_plugin().get_webui_config_schema()
        field = schema["sections"]["search_backend"]["fields"]["summarize_webpage_enabled"]
        self.assertFalse(field["default"])
        self.assertIn("summarize_webpage", field["label"])
        bindings = [(s["name"], key) for s in schema["sections"].values() for key in s["fields"]]
        self.assertEqual(len(bindings), len(set(bindings)))
        self.assertEqual([t["title"] for t in schema["layout"]["tabs"]], ["搜索", "缩写", "搜图"])


if __name__ == "__main__":
    unittest.main()
