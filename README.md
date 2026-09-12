# MAIKO-NODE-8 - MAIKO YEN Dedicated Workflow Node 8

Autonomous multi-node LLM runner node dedicated to **MAIKO YEN**, created and made by **AS**.

## Architecture & Specifications
- **Cluster**: MAIKO YEN Distributed Autonomous Cloud (30+ Nodes)
- **Lifecycle**: Continuous 5-hour auto-restart runner chain (`RESTART_INTERVAL_SECONDS: 18000`)
- **Model Engine**: `qwen-0.5b` GGUF via `llama-cpp-python` CPU engine
- **Tunneling**: Cloudflare public tunnel exposing OpenAI-standard `/v1/chat/completions`
- **Creator**: **AS**
- **Connected Frontend**: [AS Intelligence / MAIKO YEN](https://github.com/yasamarium/llm)
