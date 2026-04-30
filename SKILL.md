---
name: cnki-downloader
description: >
  从中国知网(CNKI)批量下载学术论文PDF。当用户需要下载知网论文、批量获取参考文献PDF、
  从参考文献列表下载论文、或提到"知网下载"、"CNKI下载"、"批量下载论文"、"下载参考文献"
  时使用此skill。输入可以是JSON文件(标题数组)、TXT文件(每行一个标题)、或PDF文件
  (自动提取参考文献标题)。通过Selenium连接已打开的Chrome浏览器(需开启远程调试端口9222)，
  自动搜索论文标题并下载PDF。
---

# CNKI 论文批量下载器

## 功能概述

从中国知网(CNKI)批量下载学术论文PDF。支持从多种格式读取论文标题，自动搜索并下载。

## 前置条件

1. **Chrome浏览器**需以远程调试模式启动：
   ```
   chrome.exe --remote-debugging-port=9222 --user-data-dir="你的用户数据目录"
   ```
2. 用户需在Chrome中**已登录知网**（IP登录或账号登录）
3. Python环境需安装：`selenium`, `pymupdf`(可选，用于PDF提取)

## 工作流程

### 步骤1：读取论文标题

根据输入文件格式提取标题：

- **JSON文件** (`.json`)：直接读取标题数组 `["标题1", "标题2", ...]`
- **TXT文件** (`.txt`)：每行一个标题，跳过空行
- **PDF文件** (`.pdf`)：使用pymupdf提取文本，解析参考文献中的标题

### 步骤2：连接Chrome

```python
from selenium import webdriver
options = Options()
options.debugger_address = "localhost:9222"
driver = webdriver.Chrome(options=options)
```

### 步骤3：设置知网搜索为"篇名"模式

1. 打开 `https://kns.cnki.net/kns8s/search`
2. 点击搜索框左侧的"主题"下拉按钮
3. 选择"篇名"选项

### 步骤4：逐篇搜索并下载

对每个标题：
1. 在搜索框输入标题，按回车搜索
2. 点击第一条搜索结果进入详情页
3. 滚动页面找到"PDF下载"按钮
4. 点击下载
5. 等待PDF下载完成
6. 返回搜索页继续下一篇

### 防验证策略

- 每次搜索间隔 **20秒以上**
- 页面加载后等待 **8秒**
- 下载前等待 **3秒**
- 检测到验证码时暂停60秒等待手动处理
- 使用同一标签页导航，不打开新标签页

## 运行方式

使用scripts目录下的Python脚本：

```bash
python <skill-path>/scripts/cnki_download.py --input <标题文件> --output <下载目录> --delay 20
```

参数说明：
- `--input`：输入文件路径（.json / .txt / .pdf）
- `--output`：PDF保存目录（默认：~/Downloads）
- `--delay`：搜索间隔秒数（默认：20）

## 注意事项

- 需要知网有下载权限（IP登录或机构账号）
- 部分论文可能没有PDF（仅有CAJ格式）
- 验证码触发时会暂停等待手动处理
- 下载的PDF文件名自动使用论文标题
