# CNKI Downloader

从中国知网(CNKI)批量下载学术论文PDF的Claude Code Skill。

## 功能

- 支持多种输入格式：JSON、TXT、PDF
- 自动搜索知网论文标题
- 批量下载PDF到本地
- 自动重命名PDF文件为论文标题
- 防验证策略：自动延迟、验证码检测

## 前置条件

1. **Chrome浏览器**以远程调试模式启动：
   ```bash
   chrome.exe --remote-debugging-port=9222 --user-data-dir="你的用户数据目录"
   ```

2. 在Chrome中**已登录知网**（IP登录或账号登录）

3. Python环境需安装：
   ```bash
   pip install selenium pymupdf
   ```

## 使用方法

### 命令行运行

```bash
python scripts/cnki_download.py --input 标题文件.json --output ~/Downloads --delay 20
```

参数说明：
- `--input` / `-i`：输入文件路径（.json / .txt / .pdf）
- `--output` / `-o`：PDF保存目录（默认：~/Downloads）
- `--delay` / `-d`：搜索间隔秒数（默认：20）
- `--port` / `-p`：Chrome调试端口（默认：9222）

### 输入格式

**JSON文件** (`.json`)：
```json
[
  "某体系的力学计算与某某试验对比分析",
  "某某的模拟与应用研究进展"
]
```

**TXT文件** (`.txt`)：
```
某体系的力学计算与某某试验对比分析
某某的模拟与应用研究进展
```

**PDF文件** (`.pdf`)：
自动提取参考文献中的标题。

### 在Claude Code中使用

直接说：
- "下载知网论文"
- "批量下载参考文献PDF"
- "从参考文献列表下载论文"

## 工作流程

```
Selenium连接Chrome
    ↓
读取论文标题(JSON/TXT/PDF)
    ↓
设置知网搜索为"篇名"模式
    ↓
逐篇搜索 → 进入详情页 → 点击"PDF下载"
    ↓
PDF自动下载到本地
```

## 防验证策略

- 每次搜索间隔20秒（可配置）
- 使用同一标签页导航，不打开新标签页
- 检测到验证码暂停60秒等待手动处理

## 注意事项

- 需要知网有下载权限（IP登录或机构账号）
- 部分论文可能没有PDF（仅有CAJ格式）
- 验证码触发时会暂停等待手动处理
- 下载的PDF文件名自动使用论文标题

## License

MIT
