import streamlit as st


def render_landing_section():
    st.markdown(
        """
    <div style="text-align:center;padding:40px 20px 20px 20px;">
        <h1 style="font-size:48px;font-weight:700;background:linear-gradient(135deg,#6366f1,#22c55e);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin-bottom:8px;">
            AI Travel Agent
        </h1>
        <p style="color:#71717a;font-size:18px;margin-bottom:4px;">
            Multi-Agent · Tool Calling · RAG · Memory · Streaming
        </p>
        <p style="color:#52525b;font-size:14px;">
            基于 LangGraph 构建的智能旅行规划系统
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    _render_tech_badges()
    render_agent_architecture()
    render_langgraph_flow()
    _render_key_features()


def _render_tech_badges():
    badges = [
        ("LangGraph", "#1a1a2e", "#6366f1"),
        ("DeepSeek", "#1a1a2e", "#4fc3f7"),
        ("OpenAI", "#1a1a2e", "#22c55e"),
        ("Streamlit", "#1a1a2e", "#ef4444"),
        ("RAG", "#1a1a2e", "#f59e0b"),
        ("Memory", "#1a1a2e", "#8b5cf6"),
        ("Tool Calling", "#1a1a2e", "#3b82f6"),
        ("Streaming", "#1a1a2e", "#ec4899"),
    ]
    cols = st.columns(len(badges))
    for col, (name, bg, color) in zip(cols, badges):
        with col:
            st.markdown(
                f"""
        <div style="background:{bg};border:1px solid {color}44;border-radius:20px;
                    padding:6px 0;text-align:center;">
            <span style="color:{color};font-size:13px;font-weight:600;">{name}</span>
        </div>
        """,
                unsafe_allow_html=True,
            )

    st.markdown("---")


def render_agent_architecture():
    st.subheader("🤖 Multi-Agent Architecture")
    st.caption("四个 Agent 协同工作，逐步完成旅行规划 — 点击下方按钮触发流程")

    agent_flow_svg = """
    <div style="display:flex;justify-content:center;align-items:center;gap:0;padding:20px 0;">
        <!-- Coordinator -->
        <div class="agent-node" style="animation-delay:0s;">
            <div style="background:linear-gradient(135deg,#8b5cf6,#6366f1);width:80px;height:80px;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:32px;box-shadow:0 0 20px #8b5cf666;margin:0 auto;">
                🧠
            </div>
            <div style="text-align:center;margin-top:8px;">
                <div style="font-weight:600;color:#e4e4e7;font-size:14px;">Coordinator</div>
                <div style="color:#71717a;font-size:11px;">需求理解</div>
            </div>
        </div>
        <!-- Arrow -->
        <div style="font-size:32px;color:#52525b;padding:0 8px;" class="arrow-flow">→</div>
        <!-- Researcher -->
        <div class="agent-node" style="animation-delay:0.5s;">
            <div style="background:linear-gradient(135deg,#3b82f6,#60a5fa);width:80px;height:80px;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:32px;box-shadow:0 0 20px #3b82f666;margin:0 auto;">
                🔍
            </div>
            <div style="text-align:center;margin-top:8px;">
                <div style="font-weight:600;color:#e4e4e7;font-size:14px;">Researcher</div>
                <div style="color:#71717a;font-size:11px;">信息采集</div>
            </div>
        </div>
        <!-- Arrow -->
        <div style="font-size:32px;color:#52525b;padding:0 8px;" class="arrow-flow">→</div>
        <!-- Analyst -->
        <div class="agent-node" style="animation-delay:1s;">
            <div style="background:linear-gradient(135deg,#f59e0b,#fbbf24);width:80px;height:80px;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:32px;box-shadow:0 0 20px #f59e0b66;margin:0 auto;">
                📊
            </div>
            <div style="text-align:center;margin-top:8px;">
                <div style="font-weight:600;color:#e4e4e7;font-size:14px;">Analyst</div>
                <div style="color:#71717a;font-size:11px;">数据分析</div>
            </div>
        </div>
        <!-- Arrow -->
        <div style="font-size:32px;color:#52525b;padding:0 8px;" class="arrow-flow">→</div>
        <!-- Planner -->
        <div class="agent-node" style="animation-delay:1.5s;">
            <div style="background:linear-gradient(135deg,#22c55e,#4ade80);width:80px;height:80px;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:32px;box-shadow:0 0 20px #22c55e66;margin:0 auto;">
                📋
            </div>
            <div style="text-align:center;margin-top:8px;">
                <div style="font-weight:600;color:#e4e4e7;font-size:14px;">Planner</div>
                <div style="color:#71717a;font-size:11px;">行程编排</div>
            </div>
        </div>
    </div>
    <style>
        @keyframes pulse-node {
            0%, 100% { transform: scale(1); opacity: 0.7; }
            50% { transform: scale(1.05); opacity: 1; }
        }
        .agent-node {
            animation: pulse-node 3s ease-in-out infinite;
        }
        @keyframes arrow-move {
            0%, 100% { transform: translateX(0); opacity: 0.4; }
            50% { transform: translateX(4px); opacity: 1; }
        }
        .arrow-flow {
            animation: arrow-move 1.5s ease-in-out infinite;
        }
        .agent-node:nth-child(1) { animation-delay: 0s; }
        .agent-node:nth-child(3) { animation-delay: 0.6s; }
        .agent-node:nth-child(5) { animation-delay: 1.2s; }
        .agent-node:nth-child(7) { animation-delay: 1.8s; }
    </style>
    """

    st.markdown(agent_flow_svg, unsafe_allow_html=True)

    _render_architecture_details()


def _render_architecture_details():
    details = [
        {
            "icon": "🧠",
            "title": "Coordinator Agent",
            "desc": "接收用户自然语言输入，解析旅行意图、目的地、时间、预算、偏好等结构化信息",
            "color": "#8b5cf6",
        },
        {
            "icon": "🔍",
            "title": "Researcher Agent",
            "desc": "调用百度地图搜索、天气查询、路线规划等工具，采集原始 POI 和天气数据",
            "color": "#3b82f6",
        },
        {
            "icon": "📊",
            "title": "Analyst Agent",
            "desc": "对采集数据进行评分筛选，按用户偏好聚类，生成推荐列表",
            "color": "#f59e0b",
        },
        {
            "icon": "📋",
            "title": "Planner Agent",
            "desc": "编排每日行程、分配预算、生成完整的旅行计划",
            "color": "#22c55e",
        },
    ]

    cols = st.columns(4)
    for col, d in zip(cols, details):
        with col:
            st.markdown(
                f"""
        <div style="background:#1a1a24;border:1px solid #2a2a3a;border-left:3px solid {d['color']};
                    border-radius:12px;padding:16px;height:160px;">
            <div style="font-size:28px;margin-bottom:6px;">{d['icon']}</div>
            <div style="font-weight:600;color:#e4e4e7;font-size:14px;margin-bottom:6px;">{d['title']}</div>
            <div style="color:#71717a;font-size:12px;line-height:1.5;">{d['desc']}</div>
        </div>
        """,
                unsafe_allow_html=True,
            )


def render_langgraph_flow():
    st.markdown("---")
    st.subheader("🔗 LangGraph Workflow")
    st.caption("有状态图执行引擎 — 节点=Agent，边=数据流，条件边=错误恢复")

    flow_svg = """
    <div style="display:flex;justify-content:center;padding:16px 0;">
        <svg viewBox="0 0 720 320" width="720" height="320" style="max-width:100%;height:auto;">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1"/>
                </marker>
                <marker id="arrowhead-dash" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#f59e0b"/>
                </marker>
                <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#8b5cf6"/>
                    <stop offset="100%" stop-color="#6366f1"/>
                </linearGradient>
                <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#3b82f6"/>
                    <stop offset="100%" stop-color="#60a5fa"/>
                </linearGradient>
                <linearGradient id="g3" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#f59e0b"/>
                    <stop offset="100%" stop-color="#fbbf24"/>
                </linearGradient>
                <linearGradient id="g4" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#22c55e"/>
                    <stop offset="100%" stop-color="#4ade80"/>
                </linearGradient>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
            </defs>

            <!-- Edges -->
            <line x1="160" y1="110" x2="280" y2="110" stroke="#6366f1" stroke-width="2.5"
                  marker-end="url(#arrowhead)" stroke-dasharray="6,3">
                <animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1s" repeatCount="indefinite"/>
            </line>
            <line x1="360" y1="110" x2="480" y2="110" stroke="#6366f1" stroke-width="2.5"
                  marker-end="url(#arrowhead)" stroke-dasharray="6,3">
                <animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1s" repeatCount="indefinite"/>
            </line>
            <line x1="560" y1="110" x2="680" y2="110" stroke="#6366f1" stroke-width="2.5"
                  marker-end="url(#arrowhead)" stroke-dasharray="6,3">
                <animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1s" repeatCount="indefinite"/>
            </line>

            <!-- error recovery edge -->
            <line x1="320" y1="110" x2="320" y2="250" stroke="#f59e0b" stroke-width="1.5"
                  marker-end="url(#arrowhead-dash)" stroke-dasharray="4,4" opacity="0.5"/>
            <text x="330" y="185" fill="#f59e0b" font-size="11" opacity="0.7">Error → Retry</text>

            <!-- Input node -->
            <rect x="10" y="85" width="110" height="50" rx="10" fill="#1a1a2e"
                  stroke="#71717a" stroke-width="1.5"/>
            <text x="65" y="115" fill="#e4e4e7" font-size="13" text-anchor="middle"
                  font-weight="600">📝 Input</text>

            <!-- Coordinator -->
            <rect x="115" y="80" width="90" height="60" rx="12" fill="url(#g1)" filter="url(#glow)"/>
            <text x="160" y="105" fill="white" font-size="12" text-anchor="middle"
                  font-weight="600">🧠 Coordinator</text>
            <text x="160" y="125" fill="#ddd6fe" font-size="10" text-anchor="middle">Parse Intent</text>

            <!-- Researcher -->
            <rect x="315" y="80" width="90" height="60" rx="12" fill="url(#g2)"/>
            <text x="360" y="105" fill="white" font-size="12" text-anchor="middle"
                  font-weight="600">🔍 Researcher</text>
            <text x="360" y="125" fill="#bfdbfe" font-size="10" text-anchor="middle">Tool Calls</text>

            <!-- Analyst -->
            <rect x="515" y="80" width="90" height="60" rx="12" fill="url(#g3)"/>
            <text x="560" y="105" fill="white" font-size="12" text-anchor="middle"
                  font-weight="600">📊 Analyst</text>
            <text x="560" y="125" fill="#fef3c7" font-size="10" text-anchor="middle">Analyze</text>

            <!-- Output -->
            <rect x="635" y="80" width="80" height="60" rx="10" fill="url(#g4)"/>
            <text x="675" y="105" fill="white" font-size="12" text-anchor="middle"
                  font-weight="600">📋 Plan</text>
            <text x="675" y="125" fill="#bbf7d0" font-size="10" text-anchor="middle">Output</text>

            <!-- Tool box -->
            <rect x="220" y="180" width="280" height="55" rx="10" fill="#252530"
                  stroke="#3b82f6" stroke-width="1" stroke-dasharray="5,3" opacity="0.8"/>
            <text x="360" y="202" fill="#60a5fa" font-size="11" text-anchor="middle"
                  font-weight="600">🛠️ Tool Layer</text>
            <text x="360" y="220" fill="#71717a" font-size="10" text-anchor="middle">
                BaiduMap · Weather · Route · Search
            </text>

            <!-- Tool call arrows -->
            <line x1="360" y1="140" x2="360" y2="178" stroke="#3b82f6" stroke-width="1.5"
                  marker-end="url(#arrowhead)" opacity="0.6"/>
            <line x1="360" y1="235" x2="360" y2="260" stroke="#3b82f6" stroke-width="1.5"
                  marker-end="url(#arrowhead)" opacity="0.6"/>

            <!-- RAG box -->
            <rect x="20" y="230" width="160" height="50" rx="10" fill="#252530"
                  stroke="#8b5cf6" stroke-width="1" stroke-dasharray="5,3" opacity="0.8"/>
            <text x="100" y="253" fill="#a78bfa" font-size="11" text-anchor="middle"
                  font-weight="600">📚 RAG / Memory</text>
            <text x="100" y="269" fill="#71717a" font-size="10" text-anchor="middle">
                Vector Store · Chat History
            </text>

            <!-- Memory arrow to Researcher -->
            <line x1="100" y1="228" x2="220" y2="140" stroke="#8b5cf6" stroke-width="1.2"
                  stroke-dasharray="3,3" opacity="0.4"/>
        </svg>
    </div>
    """

    st.markdown(flow_svg, unsafe_allow_html=True)

    with st.expander("📖 LangGraph 执行机制说明"):
        st.markdown(
            """
        - **StateGraph**: 有状态图，节点接收/更新全局 State
        - **顺序执行**: Coordinator → Researcher → Analyst → Planner
        - **Tool 层**: Researcher 通过 Tool Registry 调用外部 API
        - **RAG/Memory**: Planner 可查询历史行程和知识库
        - **条件边**: 任意节点出错可重试或回退
        - **Streaming**: LangGraph 支持 `stream_mode="updates"` 实时推送进度
        """
        )


def _render_key_features():
    st.markdown("---")
    st.subheader("✨ 核心技术特性")
    _render_rag_memory_entry()


def _render_rag_memory_entry():
    cols = st.columns(3)

    features = [
        {
            "icon": "🛠️",
            "title": "Tool Calling",
            "items": [
                "百度地图地理编码 (Geocoding)",
                "百度地点搜索 (Place Search)",
                "百度天气查询 (Weather Query)",
                "百度路线规划 (Direction)",
            ],
            "color": "#3b82f6",
        },
        {
            "icon": "📚",
            "title": "RAG (检索增强生成)",
            "items": [
                "FAISS 向量索引存储景点知识",
                "旅行前检索相关目的地信息",
                "基于 Embedding 的语义匹配",
                "提升 Agent 回复质量",
            ],
            "color": "#8b5cf6",
        },
        {
            "icon": "💾",
            "title": "Memory (记忆系统)",
            "items": [
                "跨会话旅行历史记录",
                "偏好自动学习与推断",
                "Session 级短期记忆",
                "用户行为持久化存储",
            ],
            "color": "#22c55e",
        },
    ]

    for col, f in zip(cols, features):
        with col:
            items_html = "".join(
                f'<li style="color:#a1a1aa;font-size:12px;margin-bottom:4px;">{item}</li>'
                for item in f["items"]
            )
            st.markdown(
                f"""
        <div style="background:#1a1a24;border:1px solid #2a2a3a;border-top:3px solid {f['color']};
                    border-radius:12px;padding:20px;height:280px;">
            <div style="font-size:32px;margin-bottom:8px;">{f['icon']}</div>
            <div style="font-weight:600;color:#e4e4e7;font-size:15px;margin-bottom:10px;">{f['title']}</div>
            <ul style="padding-left:16px;margin:0;">
                {items_html}
            </ul>
        </div>
        """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.info(
        "💡 **立即体验**: 填写上方旅行需求并点击「开始智能规划」，观看四个 Agent 逐步执行的过程。"
    )
