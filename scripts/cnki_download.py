# -*- coding: utf-8 -*-
"""
CNKI论文批量下载器
通过Selenium连接Chrome，自动搜索知网论文标题并下载PDF
"""
import sys, io, json, time, os, glob, argparse, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def load_titles(input_file):
    """从文件加载论文标题列表"""
    ext = os.path.splitext(input_file)[1].lower()

    if ext == '.json':
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    elif ext == '.txt':
        with open(input_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    elif ext == '.pdf':
        return extract_titles_from_pdf(input_file)

    else:
        print(f"不支持的文件格式: {ext}")
        return []


def extract_titles_from_pdf(pdf_path):
    """从PDF中提取参考文献标题"""
    try:
        import fitz  # pymupdf
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
    except ImportError:
        print("需要安装pymupdf: pip install pymupdf")
        return []

    # 提取参考文献部分
    ref_pattern = re.compile(r'参考文献|References|REFERENCES', re.IGNORECASE)
    match = ref_pattern.search(text)
    if match:
        text = text[match.start():]

    # 提取标题：匹配引号或书名号中的内容，以及[J]前的内容
    titles = []

    # 模式1: 匹配 [J] 前的标题
    pattern1 = re.compile(r'[\[【]([^】\]]+?)[】\]][\.\s]*\[J\]')
    for m in pattern1.finditer(text):
        title = m.group(1).strip()
        if len(title) > 5:
            titles.append(title)

    # 模式2: 匹配中文句号后的标题（带作者）
    pattern2 = re.compile(r'(?:^|\n)\d+[\.\s]+(.+?)\[J\]')
    for m in pattern2.finditer(text):
        full = m.group(1).strip()
        # 取第一个句号前的部分作为标题
        parts = re.split(r'[。\.]', full)
        if parts and len(parts[0]) > 5:
            titles.append(parts[0].strip())

    # 去重
    seen = set()
    unique = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    print(f"从PDF中提取了 {len(unique)} 个标题")
    return unique


def connect_chrome(port=9222):
    """连接到Chrome远程调试端口"""
    for attempt in range(3):
        try:
            options = Options()
            options.debugger_address = f"localhost:{port}"
            return webdriver.Chrome(options=options)
        except Exception as e:
            print(f"  连接失败({attempt+1}/3): {e}")
            time.sleep(5)
    return None


def check_verification(driver):
    """检查是否有验证码弹窗"""
    try:
        return driver.execute_script("""
            var v = document.getElementById('verify-wrap');
            if (v) {
                var s = window.getComputedStyle(v);
                if (s.display !== 'none' && s.visibility !== 'hidden') return true;
            }
            var c = document.querySelector('.verifybox-mask');
            if (c) {
                var s = window.getComputedStyle(c);
                if (s.display !== 'none') return true;
            }
            return false;
        """)
    except:
        return False


def set_title_search(driver):
    """设置搜索模式为篇名"""
    try:
        dropdown = driver.execute_script("""
            var el = document.querySelector('.sort-default');
            return el;
        """)
        if dropdown:
            dropdown.click()
            time.sleep(2)
            title_opt = driver.execute_script("""
                var els = document.querySelectorAll('a, span, li');
                for (var i = 0; i < els.length; i++) {
                    if (els[i].textContent.trim() === '篇名') return els[i];
                }
                return null;
            """)
            if title_opt:
                title_opt.click()
                time.sleep(2)
                return True
    except:
        pass
    return False


def search_by_title(driver, title):
    """在知网按标题搜索"""
    try:
        driver.get("https://kns.cnki.net/kns8s/search")
        time.sleep(8)

        if check_verification(driver):
            return None

        set_title_search(driver)

        search_box = driver.find_element(By.ID, "txt_search")
        search_box.click()
        time.sleep(1)
        search_box.clear()
        time.sleep(1)
        search_box.send_keys(title)
        time.sleep(2)
        search_box.send_keys(Keys.RETURN)
        time.sleep(8)

        if check_verification(driver):
            return None

        results = driver.execute_script("""
            var rows = document.querySelectorAll('.result-table-list tbody tr');
            var results = [];
            rows.forEach(function(row) {
                var link = row.querySelector('a.fz14');
                if (link) results.push({title: link.textContent.trim(), href: link.href});
            });
            return results;
        """)
        return results

    except Exception as e:
        print(f"  搜索出错: {e}")
        return None


def download_pdf(driver, detail_url):
    """进入详情页下载PDF"""
    try:
        driver.get(detail_url)
        time.sleep(8)

        if check_verification(driver):
            return False

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
        time.sleep(3)

        pdf_btn = driver.execute_script("""
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                if (links[i].textContent.trim() === 'PDF下载') return links[i];
            }
            return null;
        """)

        if not pdf_btn:
            return False

        download_dir = os.path.expanduser("~/Downloads")
        before = set(glob.glob(os.path.join(download_dir, "*.pdf")))

        pdf_btn.click()
        time.sleep(8)

        after = set(glob.glob(os.path.join(download_dir, "*.pdf")))
        return len(after - before) > 0

    except Exception as e:
        print(f"  下载出错: {e}")
        return False


def rename_latest_pdf(title, download_dir=None):
    """重命名最新下载的PDF"""
    if download_dir is None:
        download_dir = os.path.expanduser("~/Downloads")

    try:
        pdfs = glob.glob(os.path.join(download_dir, "*.pdf"))
        if not pdfs:
            return
        latest = max(pdfs, key=os.path.getmtime)
        clean = title
        for ch in ['/', '\\', ':', '"', '?', '<', '>', '|', '*']:
            clean = clean.replace(ch, '_')
        clean = clean[:100].strip()
        new_name = os.path.join(download_dir, f"{clean}.pdf")
        if os.path.exists(new_name):
            os.remove(new_name)
        os.rename(latest, new_name)
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description='CNKI论文批量下载器')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径(.json/.txt/.pdf)')
    parser.add_argument('--output', '-o', default=os.path.expanduser('~/Downloads'), help='PDF保存目录')
    parser.add_argument('--delay', '-d', type=int, default=20, help='搜索间隔秒数(默认20)')
    parser.add_argument('--port', '-p', type=int, default=9222, help='Chrome调试端口(默认9222)')
    args = parser.parse_args()

    # 加载标题
    titles = load_titles(args.input)
    if not titles:
        print("未找到论文标题!")
        return

    print(f"共 {len(titles)} 篇论文待下载")
    print(f"保存目录: {args.output}")
    print(f"搜索间隔: {args.delay}秒")

    # 连接Chrome
    driver = connect_chrome(args.port)
    if not driver:
        print("无法连接Chrome! 请确保Chrome已开启远程调试端口")
        return

    downloaded = []
    failed = []
    skipped = []

    print("\n" + "=" * 60)
    print("开始下载...")
    print("=" * 60)

    for i, title in enumerate(titles):
        print(f"\n[{i+1}/{len(titles)}] {title[:60]}")

        # 检查连接
        try:
            _ = driver.current_url
        except:
            print("  重新连接Chrome...")
            driver = connect_chrome(args.port)
            if not driver:
                print("  重连失败!")
                break

        # 搜索
        results = search_by_title(driver, title)

        if results is None:
            if check_verification(driver):
                print("  检测到验证码! 等待60秒手动处理...")
                time.sleep(60)
                results = search_by_title(driver, title)

        if results is None:
            print("  搜索失败")
            failed.append(title)
            time.sleep(args.delay)
            continue

        if not results:
            print("  未找到结果")
            skipped.append(title)
            time.sleep(args.delay)
            continue

        # 下载
        print(f"  找到: {results[0]['title'][:50]}")
        success = download_pdf(driver, results[0]['href'])

        if success:
            rename_latest_pdf(title, args.output)
            print("  已下载")
            downloaded.append(title)
        else:
            print("  下载失败或无PDF")
            skipped.append(title)

        # 延迟
        if i < len(titles) - 1:
            print(f"  等待{args.delay}秒...")
            time.sleep(args.delay)

    # 汇总
    print("\n" + "=" * 60)
    print("下载完成!")
    print(f"总计: {len(titles)}")
    print(f"已下载: {len(downloaded)}")
    print(f"跳过: {len(skipped)}")
    print(f"失败: {len(failed)}")
    print("=" * 60)

    if downloaded:
        print("\n已下载:")
        for t in downloaded:
            print(f"  + {t[:70]}")
    if failed:
        print("\n失败:")
        for t in failed:
            print(f"  ! {t[:70]}")


if __name__ == "__main__":
    main()
