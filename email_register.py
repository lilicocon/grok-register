"""
email_register.py — 临时邮箱入口
基于 mail_providers.py 中的提供商类，保留 Grok/x.ai 验证码提取逻辑。
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

from mail_providers import (
    CloudflareTempEmailProvider,
    DuckMailProvider,
    MailProvider,
    MailTmProvider,
    MoeMailProvider,
    TempMailLolProvider,
    YydsMailProvider,
)

# ── Config ───────────────────────────────────────────────────────────────────
_config_path = Path(__file__).parent / "config.json"
_conf: Dict[str, Any] = {}
if _config_path.exists():
    with _config_path.open("r", encoding="utf-8") as _f:
        _conf = json.load(_f)

TEMP_MAIL_PROVIDER       = str(_conf.get("temp_mail_provider") or "").strip().lower()
TEMP_MAIL_API_BASE       = str(
    _conf.get("temp_mail_api_base")
    or _conf.get("duckmail_api_base")
    or ""
).strip()
TEMP_MAIL_ADMIN_PASSWORD = str(
    _conf.get("temp_mail_admin_password")
    or _conf.get("duckmail_api_key")
    or _conf.get("duckmail_bearer")
    or ""
).strip()
TEMP_MAIL_DOMAIN         = str(_conf.get("temp_mail_domain") or _conf.get("duckmail_domain") or "").strip()
TEMP_MAIL_SITE_PASSWORD  = str(_conf.get("temp_mail_site_password", "")).strip()
PROXY                    = str(_conf.get("proxy", "")).strip()

_temp_email_cache: Dict[str, str] = {}

# ── Provider factory ─────────────────────────────────────────────────────────
_PROVIDER_LABELS: Dict[str, str] = {
    "duckmail":     "DuckMail",
    "yydsmail":     "YydsMail",
    "yyds":         "YydsMail",
    "tempmail":     "TempMail.lol",
    "tempmail_lol": "TempMail.lol",
    "mailtm":       "Mail.tm",
    "mail.tm":      "Mail.tm",
    "moemail":      "MoeMail",
    "generic":      "Temp Mail",
}


def _detect_provider_name() -> str:
    """Return explicit provider name or auto-detect from api_base hostname."""
    if TEMP_MAIL_PROVIDER:
        return TEMP_MAIL_PROVIDER
    host = (urlparse(TEMP_MAIL_API_BASE).hostname or "").lower()
    if "duckmail" in host:
        return "duckmail"
    if "215.im" in host or "yydsmail" in host:
        return "yydsmail"
    if "tempmail.lol" in host:
        return "tempmail"
    if "mail.tm" in host:
        return "mailtm"
    return "generic"


def _make_provider() -> MailProvider:
    api_base = TEMP_MAIL_API_BASE.rstrip("/")
    api_key  = TEMP_MAIL_ADMIN_PASSWORD
    domain   = TEMP_MAIL_DOMAIN
    p        = _detect_provider_name()

    if p in {"tempmail", "tempmail_lol"}:
        return TempMailLolProvider(api_key=api_key)
    if p == "duckmail":
        return DuckMailProvider(api_base=api_base or "https://api.duckmail.sbs", bearer_token=api_key)
    if p in {"yydsmail", "yyds"}:
        return YydsMailProvider(api_base=api_base, api_key=api_key, domain=domain)
    if p in {"mailtm", "mail.tm"}:
        return MailTmProvider(api_base=api_base or "https://api.mail.tm")
    if p == "moemail":
        return MoeMailProvider(api_base=api_base, api_key=api_key)
    # Generic / Cloudflare Temp Email
    return CloudflareTempEmailProvider(api_base=api_base, admin_password=api_key, domain=domain)


def _provider_label() -> str:
    return _PROVIDER_LABELS.get(_detect_provider_name(), "Temp Mail")


# ── Public API ────────────────────────────────────────────────────────────────
def get_email_and_token() -> Tuple[Optional[str], Optional[str]]:
    """创建临时邮箱并返回 (email, mail_token)。供 DrissionPage_example.py 调用。"""
    try:
        provider = _make_provider()
        email, token = provider.create_mailbox(proxy=PROXY)
        if email and token:
            _temp_email_cache[email] = token
            return email, token
        _logger.warning("[%s] create_mailbox 返回空 (email=%r, token=%r)", _provider_label(), email, token)
    except Exception as exc:
        _logger.warning("[%s] 创建邮箱失败: %s", _provider_label(), exc)
    return None, None


def get_oai_code(dev_token: str, email: str, timeout: int = 30) -> Optional[str]:
    """
    轮询收件箱获取 OTP 验证码。供 DrissionPage_example.py 调用。
    Returns: 验证码字符串（去除连字符，如 "MM0SF3"）或 None。
    """
    try:
        provider = _make_provider()
        code = provider.wait_for_otp(dev_token, email, proxy=PROXY, timeout=timeout)
        if code:
            return code.replace("-", "")
        _logger.warning("[%s] wait_for_otp 超时未收到验证码 (email=%s)", _provider_label(), email)
    except Exception as exc:
        _logger.warning("[%s] 收件失败: %s", _provider_label(), exc)
    return None


def wait_for_verification_code(mail_token: str, email: str = "", timeout: int = 120) -> Optional[str]:
    """轮询临时邮箱，等待验证码邮件。"""
    try:
        provider = _make_provider()
        code = provider.wait_for_otp(mail_token, email, proxy=PROXY, timeout=timeout)
        if code:
            print(f"[*] 从 {_provider_label()} 提取到验证码: {code}")
            return code
        _logger.warning("[%s] wait_for_otp 超时未收到验证码 (email=%s)", _provider_label(), email)
    except Exception as exc:
        _logger.warning("[%s] 收件失败: %s", _provider_label(), exc)
    return None


def extract_verification_code(content: str) -> Optional[str]:
    """
    从邮件内容提取验证码（供外部调用）。
    mail_providers._extract_code 已包含主要逻辑，此函数保留向后兼容。
    """
    from mail_providers import _extract_code
    return _extract_code(content)


# ── __main__ test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    no_wait = "--no-wait" in sys.argv

    def _log(msg: str) -> None:
        print(msg, flush=True)

    _log("=" * 60)
    _log(f"[诊断] provider  : {_detect_provider_name()!r}")
    _log(f"[诊断] api_base  : {TEMP_MAIL_API_BASE!r}")
    _log(f"[诊断] domain    : {TEMP_MAIL_DOMAIN!r}")
    _log(f"[诊断] proxy     : {PROXY!r}")
    _log("=" * 60)

    _log("\n[Step 1] 创建临时邮箱...")
    email_addr, token = get_email_and_token()
    if not email_addr or not token:
        _log("  ✗ 创建邮箱失败")
        sys.exit(1)
    _log(f"  ✓ email = {email_addr}")
    _log(f"  ✓ token = {token[:12]}...")

    if no_wait:
        _log("\n[Step 2] 跳过等待（--no-wait 模式）")
        _log("\n[诊断完成] 邮箱创建接口正常")
    else:
        _log(f"\n[Step 2] 等待邮件到达 (最长 60s)...")
        _log(f"  请向 {email_addr} 发一封任意邮件，或按 Ctrl+C 跳过")
        try:
            code = wait_for_verification_code(token, email=email_addr, timeout=60)
            if code:
                _log(f"  ✓ 提取到验证码/内容: {code}")
            else:
                _log("  ⚠ 60s 内未收到邮件（域名可能被目标站屏蔽，或邮件延迟）")
        except KeyboardInterrupt:
            _log("  跳过")
        _log("\n[诊断完成]")
