# PicSeek

> 本地图片语义搜索工具 —— 图片版 Everything

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)

用自然语言描述搜索本地图片内容。输入"海边的日落"，找到所有海边日落的照片。

**中英文双语支持** | **纯本地运行** | **零配置** | **SQLite 单文件存储**

## 工作原理

```
picseek index ~/Pictures     # 扫描图片，用 Chinese-CLIP 生成语义向量，存入 SQLite
picseek search "一只橘猫"     # 将文本转为向量，计算相似度，返回最匹配的图片
```

## 安装

```bash
# 需要 Python >= 3.10
pip install picseek
```

或从源码安装：

```bash
git clone https://github.com/Eric-meiyan/picseek.git
cd picseek
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

首次运行会自动从 HuggingFace 下载 Chinese-CLIP 模型（~700MB），之后使用本地缓存。

## 使用

### 索引图片

```bash
picseek index ~/Pictures
```

递归扫描目录，为每张图片生成语义向量。支持增量索引 —— 只处理新增和修改的文件。

### 搜索图片

```bash
# 基本搜索
picseek search "海边的日落"
picseek search "a cat sleeping on sofa"

# 限制结果数量
picseek search "会议室白板" -n 5

# 跳过目录同步（更快）
picseek search "蓝天白云" --no-sync

# 用系统预览打开结果图片
picseek search "红色跑车" --open

# 在浏览器中查看带缩略图的结果网格
picseek search "三个人站着说话" --html
```

### 查看配置

```bash
picseek config
```

## 搜索结果预览

`--html` 会生成一个带缩略图和相似度分数的网页，自动在浏览器中打开：

```bash
picseek search "户外风景" --html
```

`--open` 直接用系统默认图片查看器打开搜索到的图片：

```bash
picseek search "日落" -n 3 --open
```

## 配置

配置文件位于 `~/.picseek/config.yaml`，首次运行自动创建：

```yaml
formats:        # 支持的图片格式
  - jpg
  - jpeg
  - png
  - webp
  - bmp
  - gif

default_limit: 10          # 默认返回结果数
db_path: ~/.picseek/index.db  # 数据库路径
index_paths: []            # 已索引目录（自动维护）
```

## 技术架构

| 组件 | 选型 |
|------|------|
| 视觉语言模型 | [Chinese-CLIP](https://github.com/OFA-Sys/Chinese-CLIP) ViT-B/16 |
| 向量维度 | 512 维 float32 |
| 向量存储 | SQLite + [sqlite-vec](https://github.com/asg017/sqlite-vec) |
| CLI 框架 | Click |

### 项目结构

```
picseek/
├── cli.py        # 命令行入口
├── model.py      # Chinese-CLIP 模型加载与推理
├── indexer.py     # 索引逻辑（扫描、向量生成、入库）
├── searcher.py    # 搜索逻辑（文本向量化、相似度检索）
├── sync.py        # 目录同步（增量比对）
├── db.py          # 数据库操作
└── config.py      # 配置文件读写
```

## 性能参考

| 指标 | 数值 |
|------|------|
| 索引速度（Apple Silicon） | 20-50 张/秒 |
| 索引速度（x86 CPU） | 5-15 张/秒 |
| 每张图片向量 | ~2KB |
| 1 万张图片数据库 | ~20MB |
| 搜索耗时 | < 1 秒（不含模型加载） |

## 与其他方案的对比

| 特性 | PicSeek | Immich | PhotoMapAI | Omoide |
|------|---------|--------|------------|--------|
| 中文搜索 | **原生支持** | 有限 | 不支持 | 部分 |
| 部署复杂度 | **pip install** | Docker + PostgreSQL + Redis | Docker | Docker |
| 存储 | **SQLite 单文件** | PostgreSQL | 独立服务 | SQLite |
| 离线运行 | **完全离线** | 需要服务 | 需要服务 | 可离线 |
| 使用方式 | CLI | Web UI | Web UI | Web UI |

## 开发

```bash
git clone https://github.com/Eric-meiyan/picseek.git
cd picseek
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 运行测试
pytest
```

## License

[MIT](LICENSE)
