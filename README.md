# maimai Chart Tagger

**[English](#english)** | [中文](#chinese)

---

<a name="english"></a>

## What is this?

Upload a maimai DX chart (`maidata.txt`, `.zip`, or `.axlv`) and instantly get:

- **Skill tags** — Slide-Heavy, Stream, Trill, Stamina, Tech/Crossover, Hand-Alternation, Balanced
- **Difficulty estimate** — pulled directly from the in-game level tag when available
- **Similar songs** — matched by shared tags from a pre-built database of 1,400+ charts

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| AI Analysis | Claude claude-sonnet-4-6 (single-chart upload only) |
| Database | SQLite — pre-seeded, ships with the repo |
| Deployment | Vercel (frontend) + Railway (backend) |

## Running Locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# create backend/.env and add: ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

## Re-building the Database

If you have a local chart library, run:

```bash
cd backend
python batch_tag.py --charts-dir /path/to/charts --clear
```

Supports flat (`charts/SongName/maidata.txt`) and one-level-nested layouts (`charts/Version/SongName/maidata.txt`). Banquet charts (folders starting with `[`) are skipped automatically.

---

<a name="chinese"></a>

[English](#english) | **中文**

---

## 这是什么？

上传一个 maimai DX 铺面（`maidata.txt`、`.zip` 或 `.axlv`），立刻获得：

- **技术标签** — Slide-Heavy、Stream、Trill、Stamina、Tech/Crossover、Hand-Alternation、Balanced
- **难度估算** — 优先读取文件内的游戏内等级标签（`lv_5`/`lv_6`）
- **相似歌曲** — 从预构建的 1400+ 首铺面数据库中按标签匹配

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI (Python) |
| AI 分析 | Claude claude-sonnet-4-6（仅单首上传使用） |
| 数据库 | SQLite — 预建入库，随仓库一起提交 |
| 部署 | Vercel（前端）+ Railway（后端） |

## 本地运行

**后端**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# 创建 backend/.env，填入：ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --port 8000
```

**前端**
```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

## 重建数据库

如果你有本地铺面库，运行：

```bash
cd backend
python batch_tag.py --charts-dir /path/to/charts --clear
```

支持平铺结构（`charts/歌名/maidata.txt`）和一级嵌套结构（`charts/版本/歌名/maidata.txt`）。文件夹名以 `[` 开头的宴会铺面会自动跳过。
