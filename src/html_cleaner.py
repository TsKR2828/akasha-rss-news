"""Phase 3 — HTML / script / tracking parameter cleaner.

送入 Claude 前，先把 RSS 來源文字中的 HTML 標籤、script、style、
tracking 參數和多餘空白清掉，只留純文字。

對應規格：
- §5.3 normalized article 含 summary（可能夾帶 HTML）
- Phase 3 ROADMAP: 「RSS 進入模型前清理 HTML / script / 追蹤參數」

CLI 用法：
    python -m src.html_cleaner "some <b>HTML</b> text"
"""
from __future__ import annotations

import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# --- 追蹤參數（同 normalize.py，多加幾個常見的）---

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform", "utm_creative_format",
    "fbclid", "gclid", "gclsrc", "dclid", "gbraid", "wbraid",
    "msclkid", "twclid", "li_fat_id",
    "mc_cid", "mc_eid",
    "ref", "ref_src", "ref_url",
    "source", "s",
    "at_medium", "at_campaign",  # BBC 自家追蹤
    "ns_mchannel", "ns_source", "ns_campaign",  # BBC ns_ 系列
}


def strip_tracking_params(url: str) -> str:
    """移除 URL 中的追蹤參數。"""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        cleaned = {k: v for k, v in qs.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urlencode(cleaned, doseq=True)
        return urlunparse(parsed._replace(query=new_query, fragment=""))
    except Exception:
        return url


def clean_html(text: str) -> str:
    """把 HTML 文字轉為純文字。

    Steps:
    1. 移除 <script> 和 <style> 整塊（含內容）
    2. 移除所有 HTML 標籤
    3. 解碼常見 HTML entities
    4. 清理 URL 中的追蹤參數
    5. 壓縮多餘空白
    """
    if not text:
        return ""

    s = text

    # 1. 移除 <script>...</script> 和 <style>...</style>
    s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<style[^>]*>.*?</style>", " ", s, flags=re.DOTALL | re.IGNORECASE)

    # 2. 移除 HTML 標籤，保留內文
    s = re.sub(r"<[^>]+>", " ", s)

    # 3. 解碼常見 HTML entities
    ENTITIES = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&apos;": "'",
        "&nbsp;": " ",
        "&ndash;": "–",
        "&mdash;": "—",
        "&lsquo;": "‘",
        "&rsquo;": "’",
        "&ldquo;": "“",
        "&rdquo;": "”",
        "&hellip;": "…",
    }
    for entity, char in ENTITIES.items():
        s = s.replace(entity, char)

    # 數字 entities: &#123; 或 &#x1f;
    s = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)

    # 4. 清理文中出現的 URL 追蹤參數
    def _clean_url_match(m: re.Match) -> str:
        return strip_tracking_params(m.group(0))

    s = re.sub(r"https?://\S+", _clean_url_match, s)

    # 5. 壓縮空白
    s = re.sub(r"\s+", " ", s).strip()

    return s


def clean_article_for_rewrite(article: dict) -> dict:
    """清理 article dict 中的文字欄位，回傳 cleaned copy。"""
    cleaned = dict(article)
    for field in ("title", "summary", "content"):
        if field in cleaned and cleaned[field]:
            cleaned[field] = clean_html(cleaned[field])
    if "url" in cleaned and cleaned["url"]:
        cleaned["url"] = strip_tracking_params(cleaned["url"])
    return cleaned


# --- CLI ---

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(clean_html(" ".join(sys.argv[1:])))
    else:
        print("Usage: python -m src.html_cleaner '<p>HTML text</p>'")
