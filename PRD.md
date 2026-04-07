# PicSeek - 产品需求文档（PRD）

> 本地图片语义搜索工具 —— 图片版 Everything

## 1. 产品概述

### 1.1 产品定位

PicSeek 是一个命令行工具，能够扫描本地目录中的所有图片，利用 Chinese-CLIP 视觉语言模型为每张图片建立语义向量索引，用户通过自然语言描述（中文/英文）即可快速搜索到匹配内容的图片。

### 1.2 核心价值

传统文件搜索（如 Everything）只能按文件名搜索，无法理解图片内容。PicSeek 实现的是：**用自然语言描述来搜索图片内容**。例如输入"海边的日落"，就能找到所有包含海边日落场景的图片。

### 1.3 技术选型

| 项目 | 选型 | 说明 |
|------|------|------|
| 开发语言 | Python >= 3.10 | 生态完善，transformers、sqlite-vec 支持好 |
| 视觉语言模型 | Chinese-CLIP-B/16 (~700MB) | 中英文双语支持，一个模型覆盖两种语言；通过 HuggingFace transformers 加载 |
| 模型标识 | `OFA-Sys/chinese-clip-vit-base-patch16` | HuggingFace 模型 ID，首次运行自动下载 |
| 向量维度 | 512 维 float32 | Chinese-CLIP ViT-B/16 输出维度 |
| 向量存储 | SQLite + sqlite-vec | 单文件数据库，无需额外服务，支持向量检索 |
| 配置格式 | YAML | 可读性好，编辑方便 |
| 包管理 | uv 或 conda | 系统 Python 为 3.9.6，需通过虚拟环境使用 3.10+ |

---

## 2. 功能需求

### 2.1 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `picseek index <path>` | 索引指定目录下的所有图片 | `picseek index ~/Pictures` |
| `picseek search <描述>` | 自然语言搜索图片 | `picseek search "海边的日落"` |
| `picseek config` | 查看当前配置 | `picseek config` |

### 2.2 索引功能（`picseek index <path>`）

#### 2.2.1 基本流程

```
指定目录路径
  ↓
递归扫描所有子目录，收集匹配格式的图片文件
  ↓
与数据库已有记录比对
  ├─ 新增文件 → 用 Chinese-CLIP 生成向量 → 写入数据库
  ├─ 已删除文件 → 从数据库中删除记录
  ├─ 已修改文件（修改时间变化）→ 重新生成向量 → 更新数据库
  └─ 未变化文件 → 跳过
  ↓
输出索引统计（新增/删除/更新/跳过数量、耗时）
```

#### 2.2.2 详细规则

- 递归扫描指定目录及其所有子目录
- 仅处理配置文件中 `formats` 列表里定义的图片格式
- 格式匹配不区分大小写（`.JPG` 和 `.jpg` 均识别）
- 通过文件路径 + 修改时间判断文件是否变化
- 索引过程中显示进度条（当前/总数、百分比、预估剩余时间）
- 索引过程中遇到损坏或无法读取的图片，跳过并输出警告，不中断整体流程
- 首次索引时自动创建数据库文件

#### 2.2.3 输出示例

```
Scanning /Users/apple/Pictures ...
Found 3,521 images (jpg: 2,100, png: 980, webp: 441)

Indexing: [████████████████████████████████] 100%  3,521/3,521
  New:     3,500
  Updated: 0
  Deleted: 0
  Skipped: 21 (already indexed)
  Errors:  3 (corrupted files)

Done in 2m 35s. Database: ~/.picseek/index.db (45.2 MB)
```

#### 2.2.4 性能预期

| 指标 | 预期值 |
|------|--------|
| 索引速度（Apple Silicon Mac） | 20-50 张/秒 |
| 索引速度（普通 x86 CPU） | 5-15 张/秒 |
| 每张图片向量大小 | ~2KB（512维 float32） |
| 1 万张图片索引文件大小 | ~20MB |
| 1 万张图片索引耗时（Mac） | 3-8 分钟 |

### 2.3 搜索功能（`picseek search <描述>`）

#### 2.3.1 基本流程

```
用户输入自然语言描述
  ↓
自动同步目录变化（增量索引）
  ↓
Chinese-CLIP 将描述文本转为向量
  ↓
sqlite-vec 执行向量相似度检索
  ↓
按相似度降序输出结果（文件路径 + 相似度分数）
```

#### 2.3.2 详细规则

- 搜索前自动执行一次目录变化比对（增量同步），确保数据库与目录状态一致
- 支持中文和英文描述，无需指定语言
- 默认返回 Top N 条结果（N 由配置文件 `default_limit` 决定）
- 支持 `--limit` 参数覆盖默认返回数量
- 相似度分数范围 0-1，越接近 1 表示越匹配
- 如果数据库为空或目录不存在，给出明确提示

#### 2.3.3 输出示例

```
Syncing... (2 new, 1 deleted, 0.3s)

Results for "海边的日落":

  Score   Path
  0.92    /Users/apple/Pictures/vacation/sunset_beach.jpg
  0.87    /Users/apple/Pictures/2024/IMG_3321.png
  0.85    /Users/apple/Pictures/wallpaper/ocean_dusk.webp
  0.79    /Users/apple/Pictures/travel/golden_hour.jpg
  0.71    /Users/apple/Pictures/misc/evening_sea.jpg

5 results (0.12s)
```

#### 2.3.4 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<描述>` | 自然语言搜索词（必填） | — |
| `--limit`, `-n` | 返回结果数量 | 配置文件中的 `default_limit` |
| `--no-sync` | 跳过搜索前的目录同步 | false |

### 2.4 配置查看（`picseek config`）

输出当前生效的配置内容，方便用户确认。

---

## 3. 配置文件

### 3.1 路径

`~/.picseek/config.yaml`

首次运行时自动创建默认配置文件。

### 3.2 默认配置

```yaml
# PicSeek 配置文件

# 支持的图片格式（不区分大小写）
formats:
  - jpg
  - jpeg
  - png
  - webp
  - bmp
  - gif

# 搜索结果默认返回数量
default_limit: 10

# 索引数据库存放路径
db_path: ~/.picseek/index.db

# 索引的目录路径（index 命令执行后自动记录）
index_paths: []
```

### 3.3 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `formats` | list[str] | 支持的图片文件扩展名，用户可自行添加如 `heic`、`tiff` 等 |
| `default_limit` | int | `search` 命令默认返回的结果数量 |
| `db_path` | str | SQLite 数据库文件路径，支持 `~` 展开 |
| `index_paths` | list[str] | 已索引的目录列表，执行 `index` 命令后自动追加记录 |

---

## 4. 数据库设计

### 4.1 数据库文件

单文件 SQLite 数据库，默认路径 `~/.picseek/index.db`。

### 4.2 表结构

#### images 表（元数据）

```sql
CREATE TABLE images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_path TEXT UNIQUE NOT NULL,
  file_size INTEGER,
  modified_at REAL,
  indexed_at REAL
);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| file_path | TEXT UNIQUE NOT NULL | 图片文件绝对路径 |
| file_size | INTEGER | 文件大小（字节） |
| modified_at | REAL | 文件修改时间（Unix timestamp） |
| indexed_at | REAL | 索引时间（Unix timestamp） |

#### vec_images 虚拟表（向量检索）

```sql
CREATE VIRTUAL TABLE vec_images USING vec0(
  id INTEGER PRIMARY KEY,
  embedding float[512]
);
```

与 images 表通过 id 关联。

### 4.3 关键操作示例

#### 插入向量

```python
import struct

def serialize_f32(vector: list[float]) -> bytes:
    """将 float 列表序列化为 sqlite-vec 要求的二进制格式"""
    return struct.pack("%sf" % len(vector), *vector)

# 插入元数据
cursor.execute(
    "INSERT INTO images (file_path, file_size, modified_at, indexed_at) VALUES (?, ?, ?, ?)",
    [path, size, mtime, time.time()]
)
row_id = cursor.lastrowid

# 插入向量
cursor.execute(
    "INSERT INTO vec_images (id, embedding) VALUES (?, ?)",
    [row_id, serialize_f32(embedding)]
)
```

#### 向量相似度搜索

```python
rows = db.execute(
    """
    SELECT v.id, v.distance, i.file_path
    FROM vec_images v
    JOIN images i ON i.id = v.id
    WHERE v.embedding MATCH ?
    ORDER BY v.distance
    LIMIT ?
    """,
    [serialize_f32(query_vector), limit]
).fetchall()
```

> 注意：sqlite-vec 返回的 `distance` 是距离（越小越相似），需要转换为相似度分数展示给用户。

---

## 5. 搜索前自动同步机制

### 5.1 流程

```
读取数据库中所有已索引文件记录（file_path + modified_at）
  ↓
扫描 index_paths 中所有目录的当前文件列表
  ↓
比对差异：
  ├─ 目录中有、数据库中无 → 新增，加入待索引队列
  ├─ 数据库中有、目录中无 → 已删除，从数据库中移除
  ├─ 两者都有但 modified_at 不同 → 已修改，加入待索引队列
  └─ 两者都有且 modified_at 相同 → 无变化，跳过
  ↓
处理待索引队列（生成向量、写入数据库）
  ↓
输出同步统计（简短一行）
```

### 5.2 性能考虑

- 文件列表扫描通过 `os.scandir()` 递归实现，比 `os.walk()` 更快
- 比对逻辑在内存中进行（数据库记录加载为 dict，key 为 file_path）
- 如果无任何变化，同步过程几乎无开销
- 支持 `--no-sync` 参数跳过同步，直接搜索

---

## 6. 目录结构

```
picseek/
├── picseek/                  # Python 包
│   ├── __init__.py
│   ├── cli.py                # CLI 入口（命令解析）
│   ├── indexer.py            # 索引逻辑（扫描、向量生成、入库）
│   ├── searcher.py           # 搜索逻辑（文本向量化、相似度检索）
│   ├── sync.py               # 目录同步逻辑（增量比对）
│   ├── db.py                 # 数据库操作（SQLite + sqlite-vec）
│   ├── config.py             # 配置文件读写
│   └── model.py              # Chinese-CLIP 模型加载与推理
├── config.example.yaml       # 配置文件示例
├── requirements.txt          # Python 依赖
├── pyproject.toml            # 项目配置（支持 uv / pip 安装）
├── README.md                 # 项目说明
└── CLAUDE.md                 # Claude Code 开发指引
```

### 6.1 模型加载与推理 API

```python
from transformers import ChineseCLIPProcessor, ChineseCLIPModel
from PIL import Image

# 加载模型（首次自动下载约 700MB 到 HuggingFace 缓存目录）
model = ChineseCLIPModel.from_pretrained("OFA-Sys/chinese-clip-vit-base-patch16")
processor = ChineseCLIPProcessor.from_pretrained("OFA-Sys/chinese-clip-vit-base-patch16")
model.eval()

# 编码图片 → 512 维向量
image = Image.open("photo.jpg")
inputs = processor(images=image, return_tensors="pt")
image_features = model.get_image_features(**inputs)
image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)  # L2 归一化

# 编码文本 → 512 维向量
inputs = processor(text=["海边的日落"], padding=True, return_tensors="pt")
text_features = model.get_text_features(**inputs)
text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)  # L2 归一化
```

> Apple Silicon 可通过 `model.to("mps")` 使用 GPU 加速。如遇算子不支持，设置环境变量 `PYTORCH_ENABLE_MPS_FALLBACK=1` 回退 CPU。

---

## 7. 依赖清单

| 包 | 用途 |
|----|------|
| `transformers` | 加载 Chinese-CLIP 模型（HuggingFace） |
| `torch` | PyTorch，模型运行时 |
| `torchvision` | 图片预处理（transforms） |
| `Pillow` | 图片读取 |
| `sqlite-vec` | SQLite 向量检索扩展 |
| `click` | CLI 框架 |
| `pyyaml` | YAML 配置文件解析 |
| `tqdm` | 进度条显示 |

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 指定目录不存在 | 报错退出：`Error: Directory not found: <path>` |
| 图片文件损坏或无法读取 | 跳过并输出警告，继续处理其他文件 |
| 数据库文件不存在 | 自动创建 |
| 配置文件不存在 | 自动创建默认配置 |
| 模型文件未下载 | 首次运行时通过 HuggingFace transformers 自动下载（约 700MB），显示下载进度 |
| 数据库为空时执行搜索 | 提示：`No images indexed. Run 'picseek index <path>' first.` |
| 搜索结果为空 | 提示：`No matching images found for "<描述>".` |

---

## 9. 使用流程示例

### 9.1 首次使用

```bash
# 安装
pip install picseek

# 索引图片目录（首次运行会自动下载模型，约 700MB）
picseek index ~/Pictures

# 搜索
picseek search "一只橘猫躺在沙发上"
picseek search "sunset at beach" --limit 5
picseek search "会议室里的白板" -n 20
```

### 9.2 日常使用

```bash
# 直接搜索（自动同步目录变化）
picseek search "红色的跑车"

# 新增目录
picseek index ~/Downloads/photos

# 查看配置
picseek config

# 跳过同步，直接搜索（更快）
picseek search "蓝天白云" --no-sync
```

### 9.3 自定义配置

```bash
# 编辑配置文件添加 HEIC 支持
vim ~/.picseek/config.yaml
# 在 formats 下添加:
#   - heic
```

---

## 10. 未来扩展（不在当前版本范围内）

以下功能不在当前版本开发范围，仅作记录：

- 搜索结果自动打开图片查看器
- GUI 界面（桌面应用）
- 以图搜图（输入一张图片，找相似图片）
- Gemma 4 Vision 精排（对 CLIP 候选结果二次排序）
- 文件系统实时监听（watchdog 守护进程）
- 多用户 / 远程访问支持
