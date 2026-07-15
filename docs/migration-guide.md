# Travel-Agent 新电脑部署指南

## 1. 环境要求

- **Python**: 3.11 或更高（推荐 3.12）
- **操作系统**: Windows / macOS / Linux 均可
- **磁盘空间**: < 500 MB（含虚拟环境）

## 2. 复制项目

将整个项目文件夹复制到新电脑：

```bash
# 方式一：Git Clone（推荐）
git clone <repository-url> Travel-Agent
cd Travel-Agent

# 方式二：直接复制文件夹
# 将 Travel-Agent/ 整个目录复制到新电脑
```

**注意**：如果使用直接复制，请确保排除以下不需要的文件（见第 6 节）。

## 3. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

## 4. 安装依赖

```bash
pip install -r requirements.txt
```

这将会安装：

| 包 | 用途 |
|------|------|
| `langchain`, `langchain-core`, `langchain-openai` | LLM 调用与链式编程 |
| `langgraph` | 多 Agent 工作流引擎 |
| `pydantic`, `pydantic-settings` | 数据模型与配置 |
| `faiss-cpu` | RAG 向量检索 |
| `streamlit`, `streamlit-folium`, `folium` | 前端 UI + 地图 |
| `plotly`, `pandas` | 图表与数据分析 |
| `python-dotenv` | 环境变量加载 |
| `httpx` | HTTP 客户端 |
| `pytest`, `pytest-cov` | 测试框架 |

## 5. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的 API Key：

```ini
# 必填（至少一个生效）：
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# 可选（DeepSeek / GLM）：
# DEEPSEEK_API_KEY=...
# GLM_API_KEY=...
```

**无需 API Key 也能运行**：系统会自动使用 mock 数据和 fallback parser。

## 6. 初始化数据

### Memory 数据库

`travel_memory.db` 在项目根目录自动创建。迁移时：

- **需要保留历史记忆** → 复制 `travel_memory.db` 到新电脑项目根目录
- **不需要历史记忆** → 启动后自动创建空数据库

### RAG 知识库

知识文档位于 `src/travel_agent/knowledge/`，已包含在项目中，无需额外操作。

默认包含：北京、成都、杭州三地旅行知识（Markdown 格式）。

**扩展知识**：在 `src/travel_agent/knowledge/` 下增加 `.md` 文件即可自动加载。

### FAISS 索引

FAISS 索引在首次调用 RAG 时自动构建，无需预生成。

## 7. 启动项目

```bash
# 激活虚拟环境后：

# 启动 Streamlit 应用
streamlit run app.py

# 浏览器访问 http://localhost:8501
```

## 8. 运行测试

```bash
# 激活虚拟环境后：
python -m pytest tests/ -v

# 预期结果：67 passed
```

## 9. 需要复制的文件清单

```
Travel-Agent/
├── app.py                          ✅
├── services/agent_interface.py     ✅
├── ui/                             ✅ (全部)
├── models/state.py                 ✅
├── config/theme.py                 ✅
├── src/travel_agent/               ✅ (全部)
│   ├── agents/
│   ├── graph/
│   ├── schemas/
│   ├── tools/
│   ├── services/
│   ├── memory/
│   ├── rag/
│   └── knowledge/                  ✅ (3 个 .md 文件)
├── tests/                          ✅ (全部)
├── docs/                           ✅
├── requirements.txt                ✅
├── .env.example                    ✅
├── pyproject.toml                  ✅
└── .gitignore                      ✅
```

## 10. 不需要复制的文件

| 文件/目录 | 原因 |
|-----------|------|
| `.env` | 含 API Key，需在新电脑重新配置 |
| `travel_memory.db` | 可选 — 自动重新生成，如需历史记忆可复制 |
| `__pycache__/` | Python 缓存，自动生成 |
| `.pytest_cache/` | 测试缓存，自动生成 |
| `.venv/` | 虚拟环境，在新电脑重新创建 |
| `*.pyc` | 字节码缓存 |

## 11. 迁移后验证

```bash
# 检查 Python 版本
python --version          # 应 >= 3.11

# 检查关键包
python -c "import langgraph; print(f'langgraph {langgraph.__version__}')"
python -c "import faiss; print(f'faiss {faiss.__version__}')"
python -c "import streamlit; print(f'streamlit {streamlit.__version__}')"

# 运行测试
python -m pytest tests/ -v --tb=short

# 启动应用
streamlit run app.py
```

## 12. 常见问题

### Q: 启动时提示 `ModuleNotFoundError`

```bash
# 检查虚拟环境是否激活
which python     # macOS/Linux
where python     # Windows

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q: FAISS 安装失败

Windows 用户如果遇到 faiss 安装问题：

```bash
pip install faiss-cpu --only-binary=:all:
```

### Q: Streamlit 地图不显示

确保安装 `streamlit-folium` 和 `folium`：

```bash
pip install streamlit-folium folium
```

### Q: 无 API Key 能否运行？

**可以。** 系统在无 API Key 时会自动使用：
- Mock 工具数据（天气、POI）
- Fallback 正则解析器（意图理解）
- Mock Embedding（RAG 检索）

正常运行全部 67 个测试无需 API Key。
