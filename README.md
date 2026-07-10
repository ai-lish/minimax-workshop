# MiniMax 全功能開發者工作坊

🌐 **Live Demo**: https://ai-lish.github.io/minimax-workshop/

一個集合 MiniMax 多種 API 功能的單頁面互動工具，無需安裝，直接在瀏覽器使用。

## 功能概覽

| 功能 | 說明 |
|------|------|
| 💬 **對話助手** | 文字對話，支援模型選擇 |
| 🖼️ **視覺理解 (VLM)** | 圖片分析、OCR、文件理解 |
| 🔍 **聯網搜尋 (MCP)** | 即時資訊檢索（需 Token Plan 金鑰）|
| 🗣️ **語音合成 (TTS)** | 文字轉語音，多種聲線可選 |
| 🎵 **音樂生成** | 文字描述生成音樂 |
| 🎙️ **[Voice Buddy](voice-buddy.html) 🆕** | 多模態語音對話 (Realtime API)，廣東話/普通話/英文/日文 |
| 🧠 **提示語助手** | AI 輔助生成優質提示語 |
| 📁 **對話歷史** | 本地储存，跨分頁同步 |

## 快速開始

1. 前往 🔗 https://ai-lish.github.io/minimax-workshop/
2. 在頂部輸入你的 **MiniMax API Key**
3. 開始使用各項功能

### 取得 API Key

- MiniMax 官網：https://www.minimaxi.com/
- 標準金鑰（`sk-` 開頭）：文字對話、VLM、TTS、音樂生成
- Token Plan 金鑰（`sk-cp-` 開頭）：額外支援聯網搜尋功能

## 技術架構

- **前端**：純 HTML + Tailwind CSS（CDN）
- **圖標**：FontAwesome 6
- **存储**：sessionStorage（防窺遮蔽）
- **部署**：GitHub Pages

## 開發

```bash
# Clone
git clone https://github.com/ai-lish/minimax-workshop.git
cd minimax-workshop

# 編輯 index.html
# 推送後自動部署至 GitHub Pages
git add . && git commit -m "update" && git push
```

## 🎙️ Voice Buddy 開發者備註

Voice Buddy 用 MiniMax Realtime API 做 voice-to-voice loop。但瀏覽器嘅
native `WebSocket` **唔支援自訂 header**，所以 MiniMax 嘅
`Authorization: Bearer <key>` header 會被 silent drop。

**解決方法**：跑個本地 Python proxy (`proxy/realtime_proxy.py`)，由佢 attach
header upstream。

```bash
cd proxy/
python3 -m venv venv       # 第一次先做
./venv/bin/pip install websockets
./venv/bin/python realtime_proxy.py
# 預設 ws://127.0.0.1:8765，只聽 loopback
```

跟住瀏覽器開 `voice-buddy.html`，Proxy URL (`ws://localhost:8765`) 同
port 都寫死喺 `voice-buddy.html`，唔使改設定。

詳見 [`proxy/README.md`](proxy/README.md) 同
[`PLANNING/20260710_VOICE_BUDDY_V1.md`](PLANNING/20260710_VOICE_BUDDY_V1.md)
嘅 "Phase 7: Browser auth fix"。

---

© 2024-2026 LSC Education | 僅供教學用途