# 🌍 AI Travel Agent

基于 **LangGraph + LangChain + LLM + LBS** 的多智能体旅行规划系统。

## 架构

```
User Input → [Coordinator → Researcher → Analyst → Planner] → Travel Plan
                 ├── Memory (SQLite)
                 ├── RAG (FAISS)
                 └── Tools (Weather / POI / Route / Budget)
```

### 四个 Agent

| Agent | 职责 |
|-------|------|
| **Coordinator** 🧠 | 解析用户意图为 TravelIntent（LLM 或 fallback 正则） |
| **Researcher** 🔍 | 调用 Tool API + RAG 检索，采集天气/地点/知识 |
| **Analyst** 📊 | 评分筛选 POI，按日聚类推荐 |
| **Planner** 📋 | 编排每日行程，生成预算 |

### 模块

| 模块 | 位置 | 技术 |
|------|------|------|
| Agent 节点 | `src/travel_agent/agents/` | LangGraph node |
| 工作流 | `src/travel_agent/graph/` | LangGraph StateGraph |
| Schema | `src/travel_agent/schemas/` | Pydantic v2 |
| 工具 | `src/travel_agent/tools/` | Tool Registry + Trace |
| LLM Provider | `src/travel_agent/services/llm_client.py` | OpenAI / DeepSeek / GLM |
| Memory | `src/travel_agent/memory/` | SQLite |
| RAG | `src/travel_agent/rag/` | FAISS + Markdown |
| 前端 | `app.py` + `ui/` | Streamlit |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key（可选 — 无 key 使用 mock + fallback）

# 3. 启动应用
streamlit run app.py

# 4. 运行测试
python -m pytest tests/ -v
```

## 依赖

- Python >= 3.11
- 可选：OpenAI / DeepSeek / GLM API Key

## 项目结构

```
Travel-Agent/
├── app.py                          # Streamlit 入口
├── src/travel_agent/
│   ├── agents/                     # Agent 节点
│   ├── graph/                      # LangGraph 工作流
│   ├── schemas/                    # Pydantic 数据模型
│   ├── tools/                      # 工具注册表
│   ├── services/                   # LLM 客户端 + Runner
│   ├── memory/                     # 用户记忆 (SQLite)
│   ├── rag/                        # RAG 检索 (FAISS)
│   └── knowledge/                  # Markdown 知识文档
├── services/agent_interface.py     # 前端适配器
├── ui/                             # Streamlit 组件
├── models/state.py                 # 前端状态管理
├── tests/                          # 测试 (67+)
└── docs/                           # 文档
```

## 测试

```bash
python -m pytest tests/ -v      # 67 tests, all pass
```
