# PLANNING: MiniMax Voice Buddy V1

**Date**: 2026-07-10
**Repo**: `~/Documents/Projects/minimax-workshop/` (github.com/ai-lish/minimax-workshop)
**Type**: New sub-page in existing repo
**Status**: Awaiting Zach approval

---

## 目標 (Goals)

喺 minimax-workshop repo 內加一個 standalone sub-page `voice-buddy.html`，提供：

1. **Hybrid 對話模式** — 用戶講嘢（語音輸入），LLM 分析意思，語音回應。整個 voice-to-voice loop < 1.5 秒。
2. **即時翻譯** — 講英文/日文/普通話/廣東話，翻譯去目標語言，可選語音朗讀。
3. **語言練習 Partner** — AI 扮演對話對手，場景化練習 4 種語言，提供詞彙/文法提示。

---

## 範圍 (Scope)

| In-Scope | Out-of-Scope |
|---|---|
| Standalone HTML, CSS+JS inline（同 minimax-workshop 一致風格） | 新 GitHub repo |
| MiniMax Realtime API (WebSocket multimodal) | 登入系統 / 用戶帳戶 |
| MediaRecorder + AudioContext (browser native) | 自建 STT engine |
| localStorage API key + 對話歷史 | Server-side processing |
| 4 種語言：EN / JA / ZH-CN / YUE | 額外語言 (Korean, French, etc.) |
| 三個 mode 共用 UI | 離線 / PWA 安裝 |

---

## 架構 (Architecture)

```
Browser
├── voice-buddy.html (UI + state)
├── MediaRecorder → AudioContext → PCM 16bit/24kHz/mono → base64
├── WebSocket Client ─────────────────────────────────→ MiniMax Realtime API
│                                                       wss://api.minimax.io/ws/v1/realtime
│                                                       (or .chat fallback)
├── Event handlers:
│   - conversation.item.create (user audio)
│   - response.create (trigger assistant)
│   - session.update (config: voice, language, system prompt)
└── localStorage (API key, history, settings)
```

### MiniMax Realtime API Key Points

- **WebSocket**: `wss://api.minimax.io/ws/v1/realtime` (待 Phase 1 verify 國際版端點；fallback: `wss://api.minimax.chat/ws/v1/realtime`)
- **Audio format**: PCM, 16-bit, 24 kHz, mono, base64-encoded chunks
- **Model**: `abab6.5s-chat` (Realtime)
- **Capabilities**: audio→audio, audio→text, text→audio
- **Multilingual**: 40 種語言包括 ZH/YUE/JA/EN
- **Events**: `session.update`, `conversation.item.create`, `response.create`, `response.audio.delta`, etc.

### UI Layout

```
┌────────────────────────────────────────────────────┐
│  🔑 API Key input (top, same as workshop)         │
├────────────────────────────────────────────────────┤
│  [💬 Hybrid]  [🌐 Translate]  [🎓 Practice]        │  ← Mode tabs
├────────────────────────────────────────────────────┤
│                                                    │
│  [Active mode panel]                               │
│                                                    │
│  - Hybrid: 🎤 Push-to-talk + conversation history │
│  - Translate: source/target lang + dual display   │
│  - Practice: scenario select + partner chat       │
│                                                    │
├────────────────────────────────────────────────────┤
│  📁 History (collapsible, localStorage)           │
└────────────────────────────────────────────────────┘
```

---

## File Changes

```
minimax-workshop/
├── voice-buddy.html       ← NEW (~800 lines estimated)
├── index.html             ← EDIT: add link in nav (or new "Tools" group)
├── README.md              ← EDIT: add Voice Buddy entry
└── PLANNING/
    └── 20260710_VOICE_BUDDY_V1.md  ← THIS FILE
```

---

## Implementation Phases

### Phase 1: API 端點驗證 (blocking)
- [ ] **Verify Realtime API endpoint**: 測 `wss://api.minimax.io/ws/v1/realtime` (國際版) vs `.chat` (中文版) — 揀一個
- [ ] 從 browser test connect (WebSocket handshake)
- [ ] Test send/receive 一個 audio chunk
- [ ] Confirm 廣東話 / 日文 / 普通話 voice output 支援
- [ ] **Output**: 確定 endpoint + voice_id preset table

### Phase 2: voice-buddy.html 基本結構 (UI shell)
- [ ] Fork minimax-workshop index.html 嘅 head/body/Tailwind config
- [ ] Mode tabs (Hybrid / Translate / Practice)
- [ ] API Key input（同主頁風格）
- [ ] Push-to-talk button component
- [ ] Conversation log panel
- [ ] CSP: 加 `wss://*.minimax.io` `wss://*.minimax.chat` connect-src

### Phase 3: Hybrid 對話 mode (核心 MVP)
- [ ] MediaRecorder setup: opus → PCM 16/24k/mono conversion
- [ ] WebSocket connection lifecycle (open/session.update/close)
- [ ] Audio streaming: chunks → base64 → conversation.item.create
- [ ] Audio playback: response.audio.delta → AudioBuffer → play
- [ ] 4 語言 voice preset (EN/JA/ZH/YUE voice_id mapping)
- [ ] Conversation log (user transcript + assistant transcript)

### Phase 4: 翻譯 mode
- [ ] Source/target language dropdown (4 langs)
- [ ] Reuse Phase 3 audio input
- [ ] LLM prompt: "Translate following from {src} to {tgt}: {text}"
- [ ] Dual display panel: source text + translated text
- [ ] 可選 TTS output 翻譯結果
- [ ] Translation history

### Phase 5: 練習 Partner mode
- [ ] 場景 preset (餐廳 / 旅行 / 面試 / 日常閒聊 / 議價 / 緊急)
- [ ] Language select (EN/JA/ZH/YUE)
- [ ] System prompt 模板 (per scenario per language)
- [ ] AI persona 設定 (鼓勵/糾錯模式 toggle)
- [ ] 詞彙提示按鈕 (e.g., "How to say X in English?")
- [ ] 文法反饋 (optional, toggle-able)

### Phase 6: 整合 + 部署
- [ ] Update index.html: 加 link 到 voice-buddy.html (喺新嘅 "Voice Buddy" group 或加去 sidebar)
- [ ] Update README.md: 加 Voice Buddy 描述 + link
- [ ] Browser end-to-end 測試
- [ ] 廣東話 / 日文 / 普通話 實測 (4 語言 round-trip)
- [ ] git commit + push (auto-deploy via GitHub Pages workflow)
- [ ] Verify https://ai-lish.github.io/minimax-workshop/voice-buddy.html

---

## 安全 + 私隱 (Safety)

- **API key**: localStorage（同 minimax-workshop 風格一致，sessionStorage option 可加）
- **CSP**: 沿用 workshop 設定 + 加 Realtime WebSocket origins
- **Audio data**: 全部 browser-side processing，唔過任何 third-party proxy
- **History**: localStorage only，可一鍵清除
- **No login / no tracking / no analytics**

---

## Voice ID Preset (待 Phase 1 verify)

| 語言 | Voice ID (預設) | 模型 |
|---|---|---|
| 廣東話 (YUE) | `male Cantonese` 或 `Cantonese_2` | speech-2.8-hd |
| 普通話 (ZH-CN) | `Chinese (Mandarin)_2` | speech-2.8-hd |
| 英文 (EN) | `English_2` 或 `English_PassionateWarrior` | speech-2.8-hd |
| 日文 (JA) | `Japanese_2` | speech-2.8-hd |

*(MiniMax 提供 300+ voices，preset 會喺 Phase 1 實測後定案)*

---

## 待 Zach 確認 (Questions)

1. **Endpoint 揀邊個？** minimax.io (國際) 定 minimax.chat (中文)？我哋其他功能用 .io，咁 Realtime 都用 .io，唔通就 fallback .chat。✅ (default: 先試 .io，唔通再 fallback)

2. **MVP scope 點切？** 
   - (a) **一次過** 三個 mode (Phase 3-5 一齊做)
   - (b) **分階段**：先 Phase 3 (Hybrid)，之後先加 Translate + Practice
   - ✅ (recommended: (a)，因為架構一樣，UI tab 切換就得)

3. **語言練習 partner 嘅場景 preset** — 你想內置邊 6 個？
   - 餐廳點餐、旅行問路、面試自我介紹、議價/購物、緊急求助、日常閒聊
   - ✅ (default: 上面呢 6 個，之後可加)

4. **文件結構同意？** voice-buddy.html 喺 minimax-workshop root，index.html 加 sidebar link。✅

5. **Practice mode 反饋 toggle** — 文法/詞彙反饋係 optional 開關，定 always on？
   - ✅ (default: optional toggle，避免打斷沉浸感)

---

## 完成定義 (Done When)

- [ ] Phase 1-6 全部完成
- [ ] voice-buddy.html 可喺 `https://ai-lish.github.io/minimax-workshop/voice-buddy.html` 開到
- [ ] 4 種語言 round-trip 實測成功 (廣東話/普通話/英文/日文)
- [ ] 3 個 mode 都 work
- [ ] Mobile browser (iOS Safari) basic usability verified
- [ ] README + index.html navigation 更新

---

## 風險 + 緩解 (Risks)

| 風險 | 緩解 |
|---|---|
| Realtime API 國際版端點可能唔同 | Phase 1 先 verify，唔通用 .chat fallback |
| 廣東話 STT 質素 | 用 MiniMax Realtime（內建 STT），唔靠 Web Speech API |
| Audio latency > 2 秒 | 用 streaming chunks + early playback |
| iOS Safari MediaRecorder quirks | 用 opus/webm fallback + AudioWorklet conversion |
| API quota 用得快 | 加 session timer + cost estimate display |
| CORS issue from browser | MiniMax 已知 support browser CORS (per workshop CSP) |

---

## 開工流程 (Workflow)

1. **Zach approve** 呢個 PLANNING file ✅ (2026-07-10)
2. Phase 1 (API verify) ✅ (2026-07-10)
3. Phase 2-5 (Implementation) — 自己寫 或 delegate Codex (per AGENTS.md)
4. Phase 6 (Deploy + verify)
5. 完工後 commit message + 短 report 俾 Zach
6. **Update Hermes + OpenClaw MiniMax skills** (per Zach instruction 2026-07-10)

---

## Phase 1 Results (2026-07-10) — COMPLETED ✅

### Endpoint Verification

| Endpoint | Status | 備註 |
|---|---|---|
| `wss://api.minimax.io/ws/v1/realtime?model=abab6.5s-chat` | ✅ **WORKS** | Token Plan key (`sk-cp-`) 通，handshake ~4s |
| `wss://api.minimax.chat/ws/v1/realtime?model=abab6.5s-chat` | ❌ HANDSHAKE FAIL | 可能唔接受 Token Plan key |

### Locked Decisions

- **Endpoint**: `wss://api.minimax.io/ws/v1/realtime`
- **Model**: `abab6.5s-chat`
- **Auth**: Token Plan key (`sk-cp-`)
- **STT model in session config**: `asr-01` (MiniMax 內建，非 OpenAI whisper-1)
- **Audio format**: PCM16 (input + output)
- **Handshake latency**: ~4s first connect (acceptable for voice app)

### Test Script

`/tmp/test_realtime_ws.js` — Node.js 內建 WebSocket test，可以用嚟 re-verify 任何時候

---

## 待 Phase 3 確認

- [ ] Voice output 支援廣東話/日文/普通話 (即時 audio 返出嚟)
- [ ] VAD (voice activity detection) server-side 是否支援 push-to-talk + interrupt
- [ ] Function calling 是否需要

---

**Prepared by**: 小心 (Hermes)
**For**: Zachli
**Date**: 2026-07-10
**Last updated**: 2026-07-10 (Phase 1 complete)