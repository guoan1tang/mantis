# 设计文档: 仿 Charles 桌面应用 + AI 功能

> 日期: 2026-04-22
> 状态: 待评审

## 1. 目标

将当前的 Textual TUI 改造为仿 Charles 风格的桌面应用，保留并增强 AI 功能。解决 AI 分析慢的问题，实现异步流式输出。

## 2. 架构概览

```
Electron (Chromium) ←→ HTTP + WebSocket ←→ Python HTTP Service (aiohttp/FastAPI) ←→ mitmproxy
```

- **Python 后端**: 用 aiohttp 提供 REST API + WebSocket + SSE
- **前端**: Vite + React + TypeScript
- **通信**: HTTP API + WebSocket 实时推送流量事件
- **AI**: SSE 流式输出，避免长时间等待
- **现有代码**: Store/addon/agents 基本不动，只加 HTTP 层

## 3. UI 布局

三栏布局 + 底部 AI 面板：

```
┌───────────────────┬──────────────────────────┬─────────────────────┐
│ Domains (左侧栏)   │  Flow List (中间)         │  Request Detail (右侧)│
│ • 域名树           │  • 可筛选/排序的表格       │  • Headers           │
│ • AI 动态管理      │  • 虚拟滚动               │  • Body JSON 查看    │
│                   │  • 实时刷新               │  • Response 详情     │
├───────────────────┴──────────────────────────┴─────────────────────┤
│ AI Chat Panel (底部)                                               │
│ • 实时对话 • SSE 流式输出 • 快捷指令 • 右键 AI 操作                 │
└────────────────────────────────────────────────────────────────────┘
```

## 4. API 设计

### 4.1 安全策略

- 所有端点仅绑定 `127.0.0.1`（localhost），不暴露外部网络
- 开发阶段无需认证；未来可通过启动参数添加 `--api-token`
- Electron 通过本地端口与 Python 通信，不需要跨域

### 4.2 REST API

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/flows` | GET | 获取所有流量（支持 `?limit=N&offset=N` 分页） |
| `/api/flows/{id}` | GET | 获取单个流量详情 |
| `/api/flows/{id}/body?part=request\|response` | GET | 获取流量 Body（JSON 或 text） |
| `/api/domains` | GET/POST | 获取/添加监控域名 |
| `/api/domains/{domain}` | DELETE | 删除域名 |
| `/api/rules` | GET/POST | 获取/创建代理规则 |
| `/api/health` | GET | 服务健康检查 |

### 4.3 AI SSE 端点

所有 AI 端点使用标准 SSE 协议（`text/event-stream`），每条消息格式：

```
data: {"type": "stats", "total": 142, "domains": 3}
data: {"type": "analysis", "chunk": "正在分析..."}
data: {"type": "analysis", "chunk": "发现 90% 的请求集中..."}
data: {"type": "error", "message": "LLM 调用超时"}
data: {"type": "done"}
```

前端使用 `EventSource`（GET + 查询参数传参）或 `fetch` + 手动解析 SSE 流（POST + JSON body）。

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/ai/analyze` | POST | AI 分析流量 |
| `/api/ai/security` | POST | AI 安全检查 |
| `/api/ai/mock` | POST | AI 生成 Mock 数据 |
| `/api/ai/query` | POST | AI 通用对话（自动路由） |

请求体: `{"query": "分析流量", "flow_ids": ["...", ...]}`（flow_ids 可选，为空则分析全部）

### 4.4 WebSocket

`/ws/events` 实时推送流量事件。流量 Body 以 Base64 编码传输。

```json
{"type": "flow_added", "flow": {"id": "...", "method": "GET", "url": "...", "status_code": null, "host": "...", "path": "...", "content_type": "", "size": 0, "duration_ms": 0, "tags": []}}
{"type": "flow_updated", "flow": {"id": "...", "status_code": 200, "size": 1024, "duration_ms": 45, "response_headers": {...}, "response_body_base64": "..."}}
{"type": "domain_added", "domain": "api.example.com"}
{"type": "rule_added", "rule": {"id": "...", "description": "...", "enabled": true}}
{"type": "error", "message": "mitmproxy TLS error: ..."}
```

### 4.5 数据模型

复用现有 `FlowRecord`（`core/models.py`），字段定义见 `src/agent_proxy/core/models.py:11-28`。
新增字段: `request_body_base64`、`response_body_base64` 用于 WebSocket 传输二进制数据。

### 4.6 错误处理策略

| 场景 | 处理方式 |
|------|----------|
| Python 后端崩溃 | Electron 显示 "服务未连接" 提示，自动重试（5s 间隔，最多 3 次） |
| LLM 调用失败/超时 | SSE 推送 `{"type": "error", "message": "..."}`，前端显示错误信息 |
| mitmproxy TLS 错误 | 通过 WebSocket 推送错误事件，不影响其他请求 |
| 前端断开 | Python 端无状态，客户端重连即可恢复 |

## 5. 异步流式 AI

### 5.1 设计原则

- **本地统计立即返回**（毫秒级）：不等待 LLM
- **LLM 分析后台流式输出**（秒级）：SSE 逐块推送
- **用户随时可中断**：关闭 SSE 连接即可
- **错误可恢复**：LLM 超时/错误时推送 error 事件，不中断连接

### 5.2 AI 快捷指令

底部 AI 面板提供预设按钮，点击直接发送：
- `分析流量` → 调用 `/api/ai/analyze`
- `检查安全` → 调用 `/api/ai/security`
- `统计接口` → 调用 `/api/ai/analyze`（仅显示统计信息，不调 LLM）

### 5.3 右键 AI 操作

在流量列表右键某个请求时，弹出上下文菜单：
- `分析这个请求` → 发送该请求的 headers/body 给 LLM 分析
- `为这个接口生成 Mock` → 调用 `/api/ai/mock` 生成模拟响应
- `为此请求创建拦截规则` → 调用 RuleAgent 创建规则

### 5.4 实现流程（标准 SSE）

```python
# Python 端: aiohttp SSE
from aiohttp import web

async def ai_analyze(request):
    data = await request.json()
    query = data.get("query", "")
    flow_ids = data.get("flow_ids", [])

    resp = web.StreamResponse(
        headers={"Content-Type": "text/event-stream",
                 "Cache-Control": "no-cache",
                 "Connection": "keep-alive"}
    )
    await resp.prepare(request)

    # 1. 立即计算本地统计
    stats = compute_stats(store.flows, flow_ids)
    await resp.write(f'data: {json.dumps({"type": "stats", **stats})}\n\n')

    # 2. 后台调用 LLM
    try:
        async for chunk in llm.stream_response(build_prompt(stats, query)):
            await resp.write(f'data: {json.dumps({"type": "analysis", "chunk": chunk})}\n\n')
        await resp.write(b'data: {"type": "done"}\n\n')
    except Exception as e:
        await resp.write(f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n')

    return resp
```

```typescript
// 前端: fetch + ReadableStream 解析 SSE
const res = await fetch('/api/ai/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query, flow_ids }),
});
const reader = res.body.getReader();
// 解析 SSE 格式: "data: {...}\n\n"
```

### 5.5 数据持久化

- **流量/域名/规则**: 内存存储（复用现有 Store），进程退出后丢失
- **配置（LLM 设置等）**: 复用现有 `~/.agent-proxy/config.yaml`
- **AI 对话历史**: 仅存在于前端内存，刷新后清空
- **未来可扩展**: 流量录制保存/回放（Phase 2）

## 6. 项目结构

```
mantis/
├── src/
│   ├── agent_proxy/
│   │   ├── core/              # 现有: Store, models, config
│   │   ├── proxy/             # 现有: mitmproxy engine, addon
│   │   ├── agents/            # 现有: AI agents
│   │   ├── server/            # 新增: HTTP 服务层
│   │   │   ├── routes.py      # REST API routes
│   │   │   ├── websocket.py   # WebSocket handler
│   │   │   └── sse.py         # SSE handlers
│   │   └── cli.py             # 保留原有 TUI 入口
│   └── web/                   # 新增: Electron + Frontend
│       ├── electron/
│       │   ├── main.js        # Electron main process
│       │   └── preload.js
│       ├── src/               # React + TypeScript
│       │   ├── components/    # UI components
│       │   ├── services/      # API service
│       │   └── types/         # TypeScript types
│       ├── package.json
│       └── vite.config.ts
├── tests/
└── pyproject.toml
```

## 7. 打包与分发

- Electron: `electron-builder`
- Python: `PyInstaller` 打包成独立可执行
- 启动流程: Electron 先启动 Python 子进程 → Python 就绪 → 打开窗口
- macOS `.app` / Windows `.exe`

## 9. 现有代码影响

- **Store/addon/agents**: 不改动核心逻辑
- **cli.py**: 保留原有 TUI 入口不变，TUI 和 Electron 是互斥的启动模式
- **新增**: `server/` 模块提供 HTTP 接口
- **新增**: `web/` 目录存放 Electron 前端代码
- **测试策略**: Python server 编写单元测试（routes + SSE + WebSocket）；前端组件用 Vitest 做基础测试；Electron 到 Python 的集成测试在 Phase 2 引入

## 10. 风险与注意事项

1. **Python 进程管理**: Electron 需要正确管理 Python 子进程的生命周期
2. **端口冲突**: Python HTTP 服务需要自动选择可用端口
3. **二进制 Body**: WebSocket 传输需要考虑二进制数据编码（Base64）
4. **跨平台**: macOS/Windows 打包需要分别测试
5. **LLM 超时**: 需要设置合理的 LLM 超时时间（默认 30s），SSE 连接超时推送 error 事件
6. **Python 框架选择**: 使用 aiohttp（异步 WebSocket + SSE 支持成熟），不使用 FastAPI（需要额外 uvicorn 依赖）
