# Warframe 事件通知器（warframe-notifier）

定期輪詢社群 API（[warframestat.us](https://docs.warframestat.us/)），把**新出現**的重大事件主動推送到 **Discord**，並且不重複通知同一筆事件。

主要用途：想刷高階遺物時，能在 **Axi 虛空裂縫**出現時馬上收到提醒，不必一直手動查。

---

## 追蹤的事件

| 事件 | 預設行為 |
|------|----------|
| 虛空裂縫 Void Fissures | 只通知 **Axi 一般裂縫**（非鋼鐵之路、非虛空風暴） |
| Baro Ki'Teer 虛空商人 | 即將造訪 + 正式現身時提醒 |
| 每日突擊 Sortie | 每日輪替時通知 |
| 每週執政官狩獵 Archon Hunt | 每週輪替時通知 |
| 仲裁 Arbitration | 只通知白名單任務類型（預設 Survival/Defense/Interception/Disruption） |
| 夜光 Nightwave | 只通知週常／精英挑戰，略過每日 |
| 限時活動 Events | 新活動出現時通知 |

全部都在 [config.yaml](config.yaml) 調整，不需要改程式。

---

## 需求

- Python 3.11 以上
- 一個 Discord 頻道的 Webhook 網址

---

## 安裝與設定

### 1. 安裝依賴

```powershell
python -m pip install -r requirements.txt
```

### 2. 設定 Discord Webhook

在 Discord 頻道按 **編輯頻道 → 整合 → Webhook → 新增 Webhook → 複製 Webhook 網址**，
然後複製範本並填入網址：

```powershell
Copy-Item .env.example .env
notepad .env        # 把 DISCORD_WEBHOOK_URL 換成你複製的網址
```

> Webhook 網址等同密碼，請勿外流或上傳到 git（`.gitignore` 已排除 `.env`）。

### 3. 測試

```powershell
python run.py --notify-test       # 送一則測試訊息，確認 Discord 收得到
python run.py --once --dry-run     # 打真 API、印出「會送什麼」，但不實際送出
```

### 4.（建議）先略過目前進行中的事件

第一次正式執行時，會把「現在正在進行的所有事件」一次全部通知（約十幾則）。
若只想收**之後新出現**的事件，先執行一次 seed：

```powershell
python run.py --seed
```

### 5. 設定開機自動執行

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1
Start-ScheduledTask -TaskName WarframeNotifier     # 不必登出就先啟動
```

之後每次登入都會自動在背景常駐，每 150 秒檢查一次，有新事件就推到 Discord。
要移除：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\unregister_task.ps1
```

---

## 常用指令

| 指令 | 作用 |
|------|------|
| `python run.py --loop` | 常駐迴圈（背景服務用，預設模式） |
| `python run.py --once` | 跑一次就退出（排程器用） |
| `python run.py --once --dry-run` | 印出會送什麼，不實送、免 webhook |
| `python run.py --seed` | 把目前進行中的事件靜默標記為已通知 |
| `python run.py --notify-test` | 送一則測試通知 |

查看執行記錄：`Get-Content notifier.log -Wait -Tail 20`

---

## 設定說明（config.yaml）

- **裂縫篩選**（`name: fissures` 的 `rules`）
  - `tier_nums: [4]` → 只要 Axi（1 Lith／2 Meso／3 Neo／4 Axi／5 Requiem／6 Omnia）
  - `mission_type_keys: []` → 不限任務；要限定就填英文 key，例 `[Survival, Defense, Capture]`
  - `steel_path` / `void_storm` → 可填 `yes`／`no`／`both`
- **仲裁約每小時換一次（最吵）**：用 `mission_type_keys` 白名單與 `min_minutes_left` 壓低通知量；嫌多就把該來源設 `enabled: false`。
- **夜光**：`include_daily: false`（略過每日）、`elite_only: false`。
- **輪詢間隔**：`poll_interval_seconds: 150`（API 快取 120 秒，別設更低）。
- 任一來源都可以 `enabled: false` 關閉。

---

## 運作原理

每個輪詢週期：

```
抓取 API → 依規則過濾 → 比對 state.json 去重 → 送出 Discord 通知 → 清除過期紀錄 → 寫回 state.json
```

`state.json` 記錄「已通知過的事件」，是去重的唯一依據——所以常駐迴圈與「跑一次」行為一致，重開機也不會重複通知。
