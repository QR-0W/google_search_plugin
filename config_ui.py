"""配置页分组；只调整展示，不改变 TOML 路径或默认值。"""

from typing import Any, Dict, List, Optional


_ENGINE_LABELS = {
    "deepseek": "DeepSeek",
    "tavily": "Tavily",
    "you": "You",
    "you_news": "You Live News",
    "google": "Google",
    "bing": "Bing",
    "duckduckgo": "DuckDuckGo",
    "sogou": "搜狗",
}

_FIELD_LABELS = {
    "engine_order": "搜索引擎优先级（拖拽排序）",
    "max_results": "结果数量上限",
    "proxy": "HTTP(S) 代理",
    "fetch_content": "补充搜索结果正文",
    "summarize_webpage_enabled": "启用网页总结工具（summarize_webpage）",
    "zhihu_cookies": "知乎 Cookie",
    "timeout": "搜索超时（秒）",
    "content_timeout": "正文抓取超时（秒）",
    "max_content_length": "单页正文长度上限（字符）",
    "user_agents": "抓取 User-Agent 列表",
    "image_search_enabled": "按文字找图并发送",
    "enabled": "启用",
    "timeout_seconds": "请求超时（秒）",
    "max_retries": "重试次数上限",
    "model_name": "总结使用的模型任务",
    "temperature": "生成温度",
    "llm_timeout_seconds": "总结超时（秒）",
    "api_keys": "API 密钥列表",
    "language": "搜索语言",
    "region": "搜索区域",
    "backend": "搜索后端",
    "safesearch": "安全搜索级别",
    "timelimit": "搜索时间限制",
    "search_depth": "搜索深度",
    "include_raw_content": "返回网页原始内容",
    "include_answer": "返回服务端生成的答案",
    "topic": "搜索主题",
    "turbo": "Turbo 模式",
    "contents_enabled": "启用 Contents 正文抓取",
    "contents_format": "Contents 返回格式",
    "contents_force": "所有搜索引擎均使用 Contents",
    "images_enabled": "启用 Images（需账号权限）",
    "freshness": "搜索时间范围",
    "offset": "结果分页偏移",
    "country": "搜索国家",
    "livecrawl": "Livecrawl 范围",
    "livecrawl_formats": "Livecrawl 内容格式",
    "base_url": "API 基础地址",
    "model": "联网搜索模型",
    "max_tokens": "答案 Token 上限",
}


def build_webui_layout(schema: Dict[str, Any], engine_order: Optional[List[str]] = None) -> Dict[str, Any]:
    sections = schema["sections"]
    engine_section = sections.pop("engines")
    engine_fields = engine_section["fields"]
    backend = sections["search_backend"]
    order = engine_order if engine_order is not None else backend["fields"]["engine_order"]["default"]
    switches = {f"{engine}_enabled": label for engine, label in _ENGINE_LABELS.items()}
    engine_panels = []
    for index, engine in enumerate(order, start=1):
        fields = {
            name: field for name, field in engine_fields.items()
            if name.startswith(f"{engine}_")
            and not (engine == "you" and name.startswith("you_news_"))
        }
        panel = f"engine_{engine}"
        description = "按保存的优先级尝试；禁用或缺少必要密钥时跳过。"
        if engine == "you_news":
            description += "与 You 共用 API 密钥，需 Live News 账号权限。"
        # 多个展示面板仍绑定同一个 engines 节，保存时不迁移或复制配置。
        sections[panel] = {
            **engine_section,
            "name": "engines",
            "title": f"{index}. {_ENGINE_LABELS[engine]}",
            "description": description,
            "collapsed": True,
            "fields": fields,
        }
        engine_panels.append(panel)

    backend["title"] = "搜索设置"
    backend["description"] = "拖拽列表调整尝试顺序，保存后生效；下方引擎卡片按保存的顺序排列。"
    sections["models"]["title"] = "总结设置"
    sections["models"]["collapsed"] = True
    sections["translation"]["title"] = "缩写翻译"
    sections["actions"]["title"] = "搜图设置"
    sections["actions"]["description"] = (
        "按文字关键词找图并发送，不是以图搜图。引擎开关及密钥在搜索页统一设置；"
        "图片搜索按 You Images、Bing、搜狗、DuckDuckGo 的顺序尝试。"
    )
    sections.pop("plugin")

    for section in sections.values():
        for name, field in section["fields"].items():
            label_key = name.split("_", 1)[1] if section["name"] == "engines" else name
            if name in switches:
                field["label"] = f"启用 {switches[name]}"
            else:
                field["label"] = _FIELD_LABELS.get(label_key, field["label"])
            field["hint"] = field["hint"] or field["description"]
            if name == "zhihu_cookies":
                field["ui_type"] = "password"

    search_panels = ["search_backend", "models", *engine_panels]
    panel_order = [*search_panels, "translation", "actions"]
    for index, name in enumerate(panel_order):
        sections[name]["order"] = index
    schema["sections"] = {name: sections[name] for name in panel_order}
    schema["layout"] = {
        "type": "tabs",
        "tabs": [
            {"id": "search", "title": "搜索", "sections": search_panels},
            {"id": "translation", "title": "缩写", "sections": ["translation"]},
            {"id": "images", "title": "搜图", "sections": ["actions"]},
        ],
    }
    return schema
