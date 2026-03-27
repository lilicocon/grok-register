#!/usr/bin/env python3
"""全链路邮箱诊断：创建邮箱 → 打开注册页触发验证邮件 → 等待收件"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from email_register import get_email_and_token, wait_for_verification_code

SIGNUP_URL = "https://accounts.x.ai/sign-up?redirect=grok-com"


def log(msg: str) -> None:
    print(msg, flush=True)


def _load_browser_proxy() -> str:
    cfg_path = Path(__file__).parent / "config.json"
    if not cfg_path.exists():
        return ""
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        return str(cfg.get("browser_proxy") or cfg.get("proxy") or "").strip()
    except Exception:
        return ""


def _open_browser():
    from DrissionPage import Chromium, ChromiumOptions

    co = ChromiumOptions()
    co.auto_port()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-blink-features=AutomationControlled")
    if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
        co.set_argument("--headless=new")

    proxy = _load_browser_proxy()
    if proxy:
        co.set_argument(f"--proxy-server={proxy}")
        log(f"  浏览器代理: {proxy}")

    return Chromium(co)


def _click_email_signup(page, timeout: int = 15) -> bool:
    texts = ["使用邮箱注册", "Sign up with email", "Continue with email"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        for text in texts:
            ele = page.ele(f"text:{text}")
            if ele:
                ele.click()
                return True
        time.sleep(0.5)
    return False


def _fill_and_submit(page, email: str, timeout: int = 15) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = page.run_js(
            r"""
const email = arguments[0];
const input = Array.from(document.querySelectorAll(
    'input[type="email"], input[name="email"], input[autocomplete="email"]'
)).find(n => {
    const s = window.getComputedStyle(n);
    return s.display !== 'none' && s.visibility !== 'hidden' && !n.disabled;
});
if (!input) return 'no-input';
const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
if (setter) setter.call(input, email); else input.value = email;
const tracker = input._valueTracker;
if (tracker) tracker.setValue('');
input.dispatchEvent(new InputEvent('input', {bubbles: true, data: email}));
input.dispatchEvent(new Event('change', {bubbles: true}));
if ((input.value || '').trim() !== email) return 'fill-failed';
const btn = Array.from(document.querySelectorAll('button')).find(b => {
    const t = (b.innerText || b.textContent || '').replace(/\s+/g,'').toLowerCase();
    return t === '注册' || t.includes('注册') || t === 'signup' || t.includes('signup');
});
if (!btn || btn.disabled) return 'no-button';
btn.click();
return 'ok';
            """,
            email,
        )
        if result == "ok":
            return True
        if result in ("fill-failed", "no-button"):
            time.sleep(0.5)
            continue
        time.sleep(0.5)
    return False


def main() -> None:
    log("=" * 60)
    log("[Step 1] 创建临时邮箱...")
    email, token = get_email_and_token()
    if not email or not token:
        log("  ✗ 创建邮箱失败，请检查 temp_mail_provider 配置")
        sys.exit(1)
    log(f"  ✓ email = {email}")
    log(f"  ✓ token = {token[:12]}...")

    log(f"\n[Step 2] 打开注册页，向 {email} 触发验证邮件...")
    browser = None
    try:
        browser = _open_browser()
        page = browser.new_tab(SIGNUP_URL)
        time.sleep(2)

        log("  打开注册页，查找邮箱注册按钮...")
        if not _click_email_signup(page):
            url = getattr(page, "url", "unknown")
            title = getattr(page, "title", "unknown")
            log(f"  ✗ 未找到按钮 | url={url} | title={title}")
            log("    （可能被 Cloudflare 拦截，检查浏览器代理配置）")
            sys.exit(1)
        log("  ✓ 点击邮箱注册按钮")

        time.sleep(1)
        log("  填写邮箱并提交...")
        if not _fill_and_submit(page, email):
            log("  ✗ 未能填写邮箱或找到提交按钮")
            sys.exit(1)
        log("  ✓ 已提交，等待 x.ai 发送验证邮件...")

        # 检测域名被拒绝
        time.sleep(1.5)
        rejected = page.run_js(
            "const t = document.body?.innerText || ''; "
            "return t.includes('已被拒绝') || t.includes('been rejected') || t.includes('domain was rejected');"
        )
        if rejected:
            log("  ✗ x.ai 拒绝该邮箱域名（域名被黑名单）")
            sys.exit(1)

    except SystemExit:
        raise
    except Exception as e:
        log(f"  ✗ 浏览器操作异常: {e}")
        sys.exit(1)
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass

    log("\n[Step 3] 等待验证码邮件 (最长 90s)...")
    start = time.time()
    while True:
        elapsed = int(time.time() - start)
        code = wait_for_verification_code(token, email=email, timeout=10)
        if code:
            log(f"  ✓ 收到验证码: {code}  (耗时 {elapsed}s)")
            log("\n[诊断完成] 全链路正常 ✓")
            return
        if elapsed >= 90:
            break
        log(f"  等待中... {elapsed}s")

    log("  ✗ 90s 内未收到验证码邮件")
    log("    可能原因: x.ai 投递被屏蔽 | 邮件延迟 | 收件 API 异常")
    log("\n[诊断完成] 邮件接收失败")
    sys.exit(1)


if __name__ == "__main__":
    main()
