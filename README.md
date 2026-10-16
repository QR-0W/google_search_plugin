# Search 插件(qq:3103908461)

这是一个搜索插件，还有缩写翻译，还有图片搜索

> **v4.0.0 升级提示**：配置文件结构有调整，v3.x 用户请按本 README **🆙 v3.x → v4 升级**一节修改 `config.toml` 后再启用。

## 已更新[tavily](https://app.tavily.com)以及[You](https://you.com/platform)搜索引擎，很好用:)
tavily搜索引擎可以前往[官网](https://app.tavily.com)注册后获得密钥

You搜索引擎需要在[官网](https://you.com/platform) 获取 API Key；Live News / Images 为 early access，需账号权限）
## 以上二者均可以使用作者自建的免费注册临时[邮箱1](https://xiaowan.tech)或[邮箱2](https://mail.xiaowan.me)注册

## 📦 依赖安装

为了确保插件正常工作，您需要安装Python依赖。**在你的麦麦的运行环境**中于**本插件**的根目录下执行以下命令即可：

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

```
如果是uv安装，在pip前面加上uv即可，如uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

注意：**一键包**用户在“点我启动！！！.bat”后选择"11. 交互式安装pip模块",在其中输入requirements.txt的路径即可！（如："E:\Downloads\MaiBotOneKey\modules\MaiBot\plugins\google_search_plugin\requirements.txt"）

## 🆙 v3.x → v4 升级

如果你是从 v3.x 升级到 v4.0.0，请手动调整你的 `config.toml`（配置文件 gitignored，升级时不会被覆盖），主要有三处变化：

1. **section 重命名**：`[model_config]` → `[models]`（其中字段名不变，只是 section 名变更）
2. **新增 section**：`[translation]`（缩写翻译相关参数，不写也行，会用默认值）
3. **删除 section**：`[storage]` 整段可以删除（搜索结果现在由麦麦内部统一记录到 `tool_records`，不再由插件自己写库）
4. **`[plugin]` 段新增 `config_version = "4.0.0"`**（必填，麦麦校验配置版本时会用）

升级最快的做法：直接删掉旧 `config.toml`，让插件首次启动时自动重新生成 v4 默认配置；再把你原来的 API key / 代理 等设置项搬过去即可。

## 工作流程

1.  **接收搜索词**: planner 调用 `web_search` 时直接传入搜索关键词（或 URL），插件不再做 LLM 查询重写。
2.  **后端搜索**: 使用该关键词，调用Google、Bing、Tavily 等搜索引擎执行搜索（多引擎自动降级）。
3.  **内容抓取**: (可选) 抓取搜索结果网页的主要内容（trafilatura/readability/bs4 三级降级；知乎链接走专用抓取）。
4.  **阅读总结**: 内部LLM阅读所有搜索到的材料。
5.  **生成答案**: LLM根据阅读的材料，生成最终的总结性答案并返回。

## 🔧 配置说明

插件的配置在 `plugins/google_search_plugin/config.toml` 文件中(在第一次启动后会自动生成)。

此插件默认使用系统配置的主模型进行智能搜索，但你也可以通过以下配置项进行微调。

### `[plugin]`
- `name` (str): 插件名称，保持默认即可。
- `version` (str): 插件版本，保持默认即可。
- `config_version` (str): 配置版本号，**必填**，当前 `4.0.0`。麦麦在加载插件时会校验该字段。
- `enabled` (bool): 是否启用插件。

### `[models]`
> v3.x 中此段叫 `[model_config]`，v4 起重命名为 `[models]`（避开 Pydantic 保留名）。

- `model_name` (str, 下拉 choices): 指定用于搜索/总结的模型 task。可选：
  `replyer`, `utils`, `tool_use`, `planner`, `vlm`, `lpmm_entity_extract`, `lpmm_rdf_build`, `lpmm_qa`。默认 `replyer`。
- `temperature` (float): 单独设置本次搜索时模型的温度。默认为 0.7。

### `[actions]`
- `image_search_enabled` (bool, 默认 false): 是否启用图片搜索动作。开启后，麦麦在对话中识别到“给我看张 xx 图”之类的请求会自动调用图搜引擎并发图。关闭时该动作不会暴露给决策模型。

### `[search_backend]`
这里配置供模型调用的“后端”搜索引擎的行为。

- `engine_order` (list[str]): 搜索引擎优先级。拖动每行左侧手柄调整顺序，保存后按列表从上到下依次尝试；保留全部 8 个引擎，是否参与搜索仍由各引擎开关控制。禁用或缺少必要密钥的引擎会跳过，成功后停止接续。旧的 `default_engine` 会自动转换为保持原有行为的完整顺序。
- `max_results` (int): 每次搜索返回给模型阅读的结果数量。
- `timeout` (int): 后端搜索引擎的超时时间。
- `proxy` (str): 用于后端搜索的HTTP/HTTPS代理地址，例如 'http://127.0.0.1:7890'。默认为空字符串，表示不使用代理。
- `fetch_content` (bool): 是否抓取网页正文供模型阅读。
- `content_timeout` (int): 网页抓取的超时时间。
- `max_content_length` (int): 抓取的单个网页最大内容长度。
- `zhihu_cookies` (str): 知乎专用抓取所需的 Cookie 字符串；配置后，插件会对知乎链接启用专用抓取逻辑。
- `user_agents` (list[str]): 抓取网页时随机选用的 User-Agent 列表。

百度百科词条使用独立的匿名 Chromium 会话读取，沿用配置的代理和正文超时，不读取账号 Cookie。需要已安装 Playwright 及其 Chromium 浏览器；普通网页仍使用原有 HTTP 抓取。

KKBOX 歌曲链接通过同一歌曲 ID 的官方嵌入页读取歌曲、艺人、专辑和时长，校验歌曲 ID 并标明实际来源；嵌入页不包含原地区网页的完整歌词和专辑说明。正文补充失败时仍保留原有搜索摘要。

### `[engines]`

配置页分为「搜索」「缩写」「搜图」三页。搜索页将连接、超时和正文参数合并为「搜索设置」，模型参数集中在「总结设置」，每个搜索引擎仍各占一张可折叠卡片。引擎卡片按保存的优先级排列，实际执行直接使用同一份顺序。

每家 API 引擎只保留密钥列表；一个密钥也作为列表中的一项填写。旧的单密钥字段会在规范化时归并、去重，不会保留一份隐藏的旧值；代理、Cookie 和其他配置值保持不变。环境变量仍会额外加入对应引擎的密钥池，不写回配置文件。

引擎开关用于选择可用后端，优先级列表只控制尝试顺序，并非同时执行全部引擎。API 型后端可能消耗搜索额度。

对每个具体搜索引擎的可选配置项：

- `google_enabled` (bool, 默认 false): 是否启用 Google。
- `google_language` (str): Google 搜索语言。
- `bing_enabled` (bool, 默认 true): 是否启用 Bing。
- `bing_region` (str): Bing 区域代码。
- `sogou_enabled` (bool, 默认 true): 是否启用搜狗。
- `duckduckgo_enabled` (bool, 默认 true): 是否启用 DuckDuckGo。
- `duckduckgo_region` (str): 区域代码，例如 `wt-wt`、`us-en`。
- `duckduckgo_backend` (str): 后端，默认 `auto`。
- `duckduckgo_safesearch` (str, choices: on/moderate/off): 安全级别。
- `duckduckgo_timelimit` (str, choices: none/d/w/m/y): 时间限制，none 表示不限。
- `tavily_enabled` (bool): 是否启用 Tavily（需 API key）。
- `tavily_api_keys` (list[str]): Tavily API 密钥列表；环境变量 `TAVILY_API_KEY` 也会加入密钥池。
- `tavily_search_depth` (str, choices: basic/advanced): Tavily 搜索深度。
- `tavily_include_answer` (bool): 是否返回 Tavily 的答案。
- `tavily_include_raw_content` (bool): 是否返回网页正文片段。
- `tavily_topic` (str): 默认搜索主题，`general` 为通用检索，`news` 限定新闻。默认留空，不向 Tavily 发送 topic；单次工具调用可通过同名参数覆盖此设置，调用参数留空时仍使用后台配置。
- `tavily_turbo` (bool): Tavily Turbo 模式。
- `you_enabled` (bool): 是否启用 You Search。
- `you_news_enabled` (bool): 是否启用 You Live News（early access）。
- `you_api_keys` (list[str]): You API 密钥列表；环境变量 `YOU_API_KEY` 也会加入密钥池。
- `you_freshness` (str): 时间范围（day/week/month/year 或日期范围）。
- `you_offset` (int): 分页 offset（0-9）。
- `you_country` (str): 国家代码（如 CN/US）。
- `you_language` (str): 语言（BCP 47）。
- `you_safesearch` (str): 安全级别（off/moderate/strict）。
- `you_livecrawl` (str): livecrawl 范围（web/news/all）。
- `you_livecrawl_formats` (str): livecrawl 内容格式（html/markdown）。
- `you_contents_enabled` (bool): 是否启用 You Contents 抓取。
- `you_contents_format` (str): Contents 返回内容格式（html/markdown）。
- `you_contents_force` (bool): 强制使用 Contents，不受引擎来源限制。
- `you_images_enabled` (bool): 是否启用 You Images（early access）。
- `deepseek_enabled` (bool, 默认 false): 是否启用 DeepSeek 官方联网搜索。
- `deepseek_api_keys` (list[str]): DeepSeek API 密钥列表；环境变量 `DEEPSEEK_API_KEY` 也会加入密钥池。
- `deepseek_base_url` (str, 默认 "https://api.deepseek.com"): DeepSeek API 基础地址（支持填入代理或兼容端点，插件会自动适配 `/anthropic/v1/messages`）。
- `deepseek_model` (str, 默认 "deepseek-chat"): 调用的模型名称。
- `deepseek_max_tokens` (int, 默认 2048): DeepSeek 服务端生成答案的最大 Token 数。

### `[translation]`
缩写翻译工具（基于神奇海螺 nbnhhsh API）。

- `enabled` (bool, 默认 true): 是否启用缩写翻译工具。
- `timeout_seconds` (int, 默认 10): API 请求超时（秒）。
- `max_retries` (int, 默认 3): API 请求失败时的最大重试次数。

## 使用说明

当你向麦麦提出需要外部知识或最新信息的问题时，它会自动被触发。

### 场景

你可以像和朋友聊天一样，直接提出你的问题。

**例如：**
> "能搜一下最近很火的《Ave Mujica》吗？"
> > "我是爱厨，找一张千早爱音图片给我~"
<img src="0d116086-0df6-4694-97d3-28d521184223.png" alt="千早爱音示例" width="400">


麦麦会自动调用本插件，搜索相关信息，并给你一个总结好的答案。

### 诊断命令

启用插件后可在群/私聊里发送 `/google_search_status`，会返回插件当前的版本、模型 task、默认引擎、启用引擎清单、图片搜索/缩写翻译开关等运行状态信息，方便排查配置是否生效。

### 总结
你只需要自然地与麦麦对话，当她认为需要“上网查一下”的时候，这个插件就会被激活


---

## 鸣谢：
[MaiBot](https://github.com/MaiM-with-u/MaiBot)

感谢[heitiehu-beep](https://github.com/heitiehu-beep),[wanshangovo](https://github.com/wanshangovo)
提供的代码优化以及改进
---

## Star History

[![Star History Chart](https://api.star-history.com/image?repos=XXXxx7258/google_search_plugin&type=timeline&legend=top-left)](https://www.star-history.com/?repos=XXXxx7258%2Fgoogle_search_plugin&type=timeline&legend=top-left)
