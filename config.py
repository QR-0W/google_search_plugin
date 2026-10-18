"""google_search_plugin 配置模型。

按 PluginConfigBase 拆分为多个 section。注意 ``[models]`` section 不能叫
``model_config``——Pydantic v2 把这个名字保留给 BaseModel 的元数据属性。
"""

from typing import List, Literal

from maibot_sdk import Field, PluginConfigBase
from pydantic import field_validator

ENGINE_NAMES = (
    "deepseek", "tavily", "you", "you_news", "google", "bing", "duckduckgo", "sogou",
)


def legacy_engine_order(default_engine: str) -> List[str]:
    if default_engine not in ENGINE_NAMES:
        raise ValueError("旧配置中的默认搜索引擎无效")
    return sorted(ENGINE_NAMES, key=lambda name: name != default_engine)

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


class PluginSection(PluginConfigBase):
    """插件基础信息"""

    __ui_label__ = "插件"
    __ui_icon__ = "package"
    __ui_order__ = 0

    name: str = Field(default="google_search", description="插件名称")
    version: str = Field(default="4.0.6", description="插件版本")
    config_version: str = Field(default="4.0.0", description="配置版本(Runner 用于兼容性校验)")
    enabled: bool = Field(default=True, description="是否启用插件")


class ModelsSection(PluginConfigBase):
    """搜索/总结使用的 LLM 任务参数。

    section 名为 ``models`` 而非 ``model_config``——后者被 Pydantic v2 保留为
    BaseModel 的元数据属性,不能用作字段名。
    """

    __ui_label__ = "模型"
    __ui_icon__ = "brain"
    __ui_order__ = 1

    model_name: Literal[
        "replyer",
        "utils",
        "planner",
        "vlm",
    ] = Field(
        default="replyer",
        description=(
            "指定用于搜索和总结的系统模型 task。可选值与 host model_configs.py "
            "里的 chat 类 task 对齐(replyer/utils/planner/vlm),默认 'replyer'。"
        ),
    )
    temperature: float = Field(default=0.7, description="模型生成温度")
    llm_timeout_seconds: int = Field(
        default=60,
        description="单次 LLM 调用超时(秒);避免模型卡住时整个搜索 Tool 阻塞",
    )


class ActionsSection(PluginConfigBase):
    """动作组件开关"""

    __ui_label__ = "动作"
    __ui_icon__ = "zap"
    __ui_order__ = 2

    image_search_enabled: bool = Field(
        default=False,
        description="按文字关键词找图并向聊天发送一张图片，不是以图搜图。可用后端随引擎开关变化。",
    )


class SearchBackendSection(PluginConfigBase):
    """搜索后端通用参数"""

    __ui_label__ = "搜索后端"
    __ui_icon__ = "globe"
    __ui_order__ = 3

    engine_order: List[str] = Field(
        default_factory=lambda: legacy_engine_order("bing"),
        description="拖动每行左侧手柄调整尝试顺序；保留全部引擎名称，是否启用在各引擎卡片中设置。",
        json_schema_extra={"min_items": len(ENGINE_NAMES), "max_items": len(ENGINE_NAMES)},
    )

    @field_validator("engine_order")
    @classmethod
    def validate_engine_order(cls, value: List[str]) -> List[str]:
        if len(value) != len(ENGINE_NAMES) or set(value) != set(ENGINE_NAMES):
            raise ValueError("搜索顺序必须包含全部 8 个引擎且不重复，请拖拽排序，不要修改引擎名称")
        return value

    max_results: int = Field(default=15, description="默认返回结果数量")
    timeout: int = Field(default=20, description="搜索超时时间(秒)")
    proxy: str = Field(
        default="",
        description="HTTP/HTTPS 代理地址,例如 'http://127.0.0.1:7890'。留空表示不走代理。",
    )
    summarize_webpage_enabled: bool = Field(
        default=False,
        description="向 Planner 提供 summarize_webpage 网页总结工具，默认关闭；不影响搜索结果正文补充。",
    )
    fetch_content: bool = Field(default=True, description="是否抓取网页内容")
    content_timeout: int = Field(default=10, description="内容抓取超时(秒)")
    max_content_length: int = Field(default=3000, description="最大内容长度")
    zhihu_cookies: str = Field(
        default="",
        description="知乎专用抓取使用的 Cookie 字符串;留空则不启用知乎专用抓取。",
    )
    user_agents: list[str] = Field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        ],
        description="抓取网页时使用的 User-Agent 列表,会从中随机选择。",
    )


class EnginesSection(PluginConfigBase):
    """各搜索引擎的开关与专属参数"""

    __ui_label__ = "引擎"
    __ui_icon__ = "settings"
    __ui_order__ = 4

    # Google
    google_enabled: bool = Field(default=False, description="是否启用 Google 搜索")
    google_language: str = Field(default="zh-cn", description="搜索语言")

    # Bing
    bing_enabled: bool = Field(default=True, description="是否启用 Bing 搜索")
    bing_region: str = Field(default="zh-CN", description="Bing 搜索区域代码")

    # 搜狗
    sogou_enabled: bool = Field(default=True, description="是否启用搜狗搜索")

    # DuckDuckGo (DDGS)
    duckduckgo_enabled: bool = Field(default=True, description="是否启用 DDGS 元搜索引擎")
    duckduckgo_region: str = Field(default="wt-wt", description="搜索区域代码,例如 'us-en' 或 'cn-zh'")
    duckduckgo_backend: str = Field(
        default="auto",
        description="使用的后端。'auto' 表示自动选择,也可以指定多个,如 'duckduckgo,google,brave'",
    )
    duckduckgo_safesearch: Literal["on", "moderate", "off"] = Field(
        default="moderate",
        description="安全搜索级别",
    )
    duckduckgo_timelimit: Literal["none", "d", "w", "m", "y"] = Field(
        default="none",
        description="时间限制 (d, w, m, y;none 表示不限)",
    )

    # Tavily
    tavily_enabled: bool = Field(default=False, description="是否启用 Tavily 搜索")
    tavily_api_keys: list[str] = Field(
        default_factory=list,
        description="Tavily API key 列表,填写多个时随机选用",
    )
    tavily_search_depth: Literal["basic", "advanced"] = Field(default="basic", description="搜索深度")
    tavily_include_raw_content: bool = Field(default=False, description="是否返回网页原始内容")
    tavily_include_answer: bool = Field(default=True, description="是否返回 Tavily 生成的答案")
    tavily_topic: str = Field(
        default="",
        description=(
            "默认主题：general 为通用检索，news 限定新闻；留空表示不传 topic。"
            "单次工具调用可覆盖此设置。"
        ),
    )
    tavily_turbo: bool = Field(default=False, description="是否启用 Tavily Turbo 模式")

    # You
    you_enabled: bool = Field(default=False, description="是否启用 You Search")
    you_news_enabled: bool = Field(default=False, description="是否启用 You Live News(early access)")
    you_api_keys: list[str] = Field(
        default_factory=list,
        description="You API key 列表,填写多个时随机选用",
    )
    you_freshness: str = Field(
        default="",
        description="You 搜索时间范围(可选:day/week/month/year;留空表示不限)",
    )
    you_offset: int = Field(default=0, description="You 搜索分页 offset(0-9,超出将被夹取)")
    you_country: str = Field(default="", description="You 搜索国家代码(如 CN/US)")
    you_language: str = Field(default="", description="You 搜索语言(BCP 47,如 EN/zh-Hans)")
    you_safesearch: str = Field(
        default="",
        description="You 安全搜索级别(off/moderate/strict;留空表示使用默认值)",
    )
    you_livecrawl: str = Field(
        default="",
        description="You Livecrawl 范围(web/news/all);留空表示不启用",
    )
    you_livecrawl_formats: str = Field(
        default="",
        description="You Livecrawl 内容格式(html/markdown);留空表示不启用",
    )
    you_contents_enabled: bool = Field(default=False, description="是否启用 You Contents 抓取")
    you_contents_format: Literal["html", "markdown"] = Field(
        default="markdown",
        description="You Contents 返回内容格式",
    )
    you_contents_force: bool = Field(
        default=False,
        description="是否强制使用 You Contents(不受搜索引擎来源限制)",
    )
    you_images_enabled: bool = Field(default=False, description="是否启用 You Images(early access)")

    # DeepSeek
    deepseek_enabled: bool = Field(default=False, description="是否启用 DeepSeek 官方联网搜索")
    deepseek_api_keys: list[str] = Field(
        default_factory=list,
        description="DeepSeek API key 列表,填写多个时随机选用",
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API 基础地址（自动适配 /anthropic/v1/messages 端点）",
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="DeepSeek 调用的模型名称（默认 deepseek-chat）",
    )
    deepseek_max_tokens: int = Field(
        default=2048,
        description="DeepSeek 生成答案的最大 Token 数",
    )


class TranslationSection(PluginConfigBase):
    """缩写翻译(神奇海螺 nbnhhsh)参数"""

    __ui_label__ = "缩写翻译"
    __ui_icon__ = "languages"
    __ui_order__ = 6

    enabled: bool = Field(default=True, description="是否启用缩写翻译工具")
    timeout_seconds: int = Field(default=10, description="API 请求超时(秒)")
    max_retries: int = Field(default=3, description="API 请求失败时的最大重试次数")


# ---------------------------------------------------------------------------
# Top-level plugin config
# ---------------------------------------------------------------------------


class GoogleSearchPluginConfig(PluginConfigBase):
    """google_search_plugin 顶层配置"""

    plugin: PluginSection = Field(default_factory=PluginSection)
    models: ModelsSection = Field(default_factory=ModelsSection)
    actions: ActionsSection = Field(default_factory=ActionsSection)
    search_backend: SearchBackendSection = Field(default_factory=SearchBackendSection)
    engines: EnginesSection = Field(default_factory=EnginesSection)
    translation: TranslationSection = Field(default_factory=TranslationSection)
