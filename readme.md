# Grok Register

面向 `x.ai` 注册批处理的一体化项目，提供控制台、注册执行器、WARP 网络出口、`grok2api` token 落池和运行时环境。

## 功能

- 命令行直接跑注册
- 在 Web 控制台里创建批量任务并保存系统默认配置
- 给每个任务独立配置出口、临时邮箱参数和 sink
- 控制台内置环境健康检查和邮箱全链路诊断
- 实时查看每个任务的状态、轮次、成功数、失败数和日志
- 注册成功后自动推送至 `grok2api` 兼容接口
- 内置临时邮箱适配层：支持 TempMail.lol、DuckMail、YydsMail、Mail.tm、MoeMail、Cloudflare 共 6 类 provider，留空时按 `temp_mail_api_base` hostname 自动识别

## 先决条件

这个项目要跑通，至少要有下面 3 个外部条件：

- 可用的网络出口（代理）
- 可被 `x.ai` 接受的临时邮箱域名
- 可接收 token 的下游 sink，例如 `grok2api`

现在仓库已经内置：

- `warp`：默认网络出口
- `grok2api`：默认 token sink（OpenAI 兼容接口桥，用于接收和管理注册得到的 SSO token）

所以新部署时，你不需要再额外去拉其它仓库拼接。你还需要自己准备的，主要是临时邮箱 API 和对应域名。

## 最快启动方式

推荐第一次使用直接走 Docker。

```bash
git clone https://github.com/509992828/grok-register.git
cd grok-register
cp .env.example .env
docker compose up -d --build
```

如果需要改外网端口或 `grok2api` 后台口令，先编辑 `.env`。

`docker-compose.yml` 默认会启动：

- `warp`：`caomingjun/warp:latest`，容器内默认 SOCKS5 地址为 `socks5://warp:1080`，宿主机映射 `127.0.0.1:1080`
- `grok2api`：`ghcr.io/chenyme/grok2api:latest`，默认端口 `8000`
- `console`：基于 `apps/worker-runtime/Dockerfile` 构建，默认端口 `18600`

启动后访问：

- `http://<你的服务器IP>:18600`
- `http://<你的服务器IP>:8000/admin`

然后在控制台里填写：

- `temp_mail_provider`（选择临时邮箱服务类型，或留空自动检测）
- `temp_mail_api_base`
- `temp_mail_admin_password`
- `temp_mail_domain`

其中 DuckMail 的推荐填法是：

- `temp_mail_provider`: `duckmail`
- `temp_mail_api_base`: `https://api.duckmail.sbs`
- `temp_mail_admin_password`: 可留空；如果你要使用 DuckMail 私有域名，再填 Bearer Token
- `temp_mail_domain`: 可留空；留空时执行器会自动挑一个 DuckMail 公开可用域名

默认情况下：

- `browser_proxy` 和 `proxy` 已经预设为容器内的 `warp`
- `api.endpoint` 和 `api.token` 已经预设为容器内的 `grok2api`

所以第一次部署时，你通常只需要补全临时邮箱这一组参数。

## 宿主机启动方式

```bash
cp config.example.json config.json
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb chromium-browser
./deploy/start-console.sh
```

默认监听 `0.0.0.0:18600`。

宿主机模式最容易漏的就是浏览器依赖，至少补齐这 3 项：

- `pip install -r requirements.txt`，这里已经包含 `pyvirtualdisplay`
- `apt install xvfb`
- `apt install chromium-browser` 或自行安装 `google-chrome-stable`

如果你只想先把内置网络和 sink 起起来，也可以执行：

```bash
cp .env.example .env
docker compose up -d warp grok2api
```

## 命令行验证

在真正跑批之前，建议先用一次单轮验证检查链路：

```bash
cp config.example.json config.json
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb chromium-browser
python DrissionPage_example.py --count 1
```

## 邮箱链路诊断

如果你只想先验证"邮箱 API + 浏览器出口 + `x.ai` 注册页 + OTP 收件"这条链路，而不是直接跑完整注册，可以执行：

```bash
python diagnose.py
```

`diagnose.py` 会按下面顺序做一次全链路检查：

1. 创建临时邮箱
2. 启动 Chromium
3. 打开 `https://accounts.x.ai/sign-up?redirect=grok-com`
4. 点击邮箱注册入口，填写邮箱并提交
5. 检测当前域名是否被 `x.ai` 直接拒绝
6. 轮询验证码邮件，最长等待 90s

在 Web 控制台里点击「开始诊断」时，后台调用的也是这个脚本，并通过 `/api/diagnose/email` 以 SSE 实时回传输出。

## 当前配置模板

```json
{
  "run": {
    "count": 50
  },
  "temp_mail_provider": "",
  "temp_mail_api_base": "https://mail-api.example.com",
  "temp_mail_admin_password": "<your_admin_password>",
  "temp_mail_domain": "mail.example.com",
  "temp_mail_site_password": "",
  "proxy": "",
  "browser_proxy": "",
  "api": {
    "endpoint": "http://127.0.0.1:8000/v1/admin/tokens",
    "token": "",
    "append": true
  }
}
```

配置模板说明：

- 仓库里提供的是可公开分享的示例配置，不包含任何真实邮箱接口、真实域名、密码或 token
- `temp_mail_provider` 可选 `tempmail | duckmail | yydsmail | mailtm | moemail | generic`；留空时 `email_register.py` 会按 `temp_mail_api_base` 的 hostname 自动识别
- `temp_mail_admin_password` 的含义跟提供商有关，可能是 Bearer Token、API Key 或自部署管理口令
- `temp_mail_domain` 对 `duckmail`、`mailtm` 可以留空；`generic` / Cloudflare Temp Email 一般需要填写
- `temp_mail_site_password` 仅给 generic 兼容接口预留；其余 provider 通常忽略
- `proxy` 给临时邮箱 API 请求使用，`browser_proxy` 给 Chromium 访问 `x.ai` 使用
- 实际运行时，请把你自己的参数写进本机 `config.json` 或控制台系统配置里，不要把生产凭据提交回仓库
- 代码兼容旧版 `duckmail_*` 字段；现在也原生支持把 DuckMail 直接接到 `temp_mail_*` 这一套字段上

## 临时邮箱提供商

`mail_providers.py` 定义了 `MailProvider` 抽象基类以及 6 个具体实现，`email_register.py` 负责 provider factory 和自动检测逻辑。`temp_mail_provider` 留空时，`email_register.py` 会按 `temp_mail_api_base` 的 hostname 推断 provider，但仅 `tempmail`、`duckmail`、`yydsmail`、`mailtm` 四类支持 hostname 自动识别；`moemail` 必须显式设置 `"temp_mail_provider": "moemail"`，其余自部署接口默认按 `generic` 处理。外部调用统一走 `get_email_and_token()`、`get_oai_code()`、`wait_for_verification_code()`，失败时会写入 `logging.warning()`。

| 提供商 | `temp_mail_provider` | API Base | 鉴权方式 | 域名策略 |
| --- | --- | --- | --- | --- |
| TempMail.lol | `tempmail` | `https://api.tempmail.lol/v2` | `Authorization: Bearer <api_key>`（免费模式可留空） | 自动分配 |
| DuckMail | `duckmail` | `https://api.duckmail.sbs` | 可选 Bearer Token | 自动从 `/domains` 选公开域名 |
| YydsMail | `yydsmail` | `https://maliapi.215.im` | `AC-xxx` API Key | `temp_mail_domain` 可选 |
| Mail.tm | `mailtm` | `https://api.mail.tm` | 无需预置 Key（自动注册账户） | 自动拉取 `/domains` |
| MoeMail | `moemail` | 自部署地址 | `X-API-Key` | 从 `/api/config` 动态读取 |
| Cloudflare Temp Email | `generic` | 自部署地址 | `temp_mail_admin_password` 管理口令 | `temp_mail_domain` 必填 |

下面给出每种 provider 的最小配置示例。

### TempMail.lol

```json
{
  "temp_mail_provider": "tempmail",
  "temp_mail_admin_password": "tempmail.xxxxxxxx.your_api_key",
  "temp_mail_domain": "",
  "temp_mail_site_password": ""
}
```

### DuckMail

```json
{
  "temp_mail_provider": "duckmail",
  "temp_mail_api_base": "https://api.duckmail.sbs",
  "temp_mail_admin_password": "",
  "temp_mail_domain": ""
}
```

> 当前实现自动从 `/domains` 选择公开域名，`temp_mail_domain` 留空即可，填了也会被忽略。

### YydsMail

```json
{
  "temp_mail_provider": "yydsmail",
  "temp_mail_api_base": "https://maliapi.215.im",
  "temp_mail_admin_password": "AC-your_api_key",
  "temp_mail_domain": ""
}
```

### Mail.tm

```json
{
  "temp_mail_provider": "mailtm",
  "temp_mail_api_base": "https://api.mail.tm",
  "temp_mail_admin_password": "",
  "temp_mail_domain": ""
}
```

> 当前实现自动拉取 `/domains` 并创建临时账户，无需预先配置域名或密码，`temp_mail_domain` 留空即可。

### MoeMail（自部署）

```json
{
  "temp_mail_provider": "moemail",
  "temp_mail_api_base": "https://your-moemail-instance.example.com",
  "temp_mail_admin_password": "your_api_key",
  "temp_mail_domain": ""
}
```

### Cloudflare Temp Email / Generic（自部署）

```json
{
  "temp_mail_provider": "generic",
  "temp_mail_api_base": "https://mail-api.example.com",
  "temp_mail_admin_password": "<your_admin_password>",
  "temp_mail_domain": "mail.example.com",
  "temp_mail_site_password": ""
}
```

## Web 控制台

`apps/console/app.py` 基于 FastAPI，把根目录注册脚本包装成"可创建、可观察、可停止、可删除"的批处理系统。

- **系统默认配置**：在控制台保存后会原子写回根目录 `config.json`
- **任务生命周期**：`queued → running → completed / failed / partial / stopping / stopped`
- **隔离执行**：每个任务在 `apps/console/runtime/tasks/task_<id>/` 下独立运行，自动复制核心脚本（`DrissionPage_example.py`、`email_register.py`、`mail_providers.py`）和 `turnstilePatch/` 目录，写入任务级 `config.json` 后启动子进程
- **健康检查**：`/api/health` 探测 `WARP / 代理连通性`、`grok2api Sink`、`Temp Mail API`、`x.ai 注册页`
- **邮箱诊断**：`/api/diagnose/email` 通过 SSE 流式输出 `diagnose.py` 的诊断过程
- **实时日志**：前端轮询 `/api/tasks/{id}/logs`，展示成功数、失败数、当前阶段和最近日志

## 文档入口

- 新手快速上手：[docs/quickstart.md](docs/quickstart.md)
- 完整业务链路：[docs/business-flow.md](docs/business-flow.md)
- 配置字段说明：[docs/options.md](docs/options.md)
- 临时邮箱接口要求：[docs/temp-mail-api.md](docs/temp-mail-api.md)
- 模块边界和架构：[docs/architecture.md](docs/architecture.md)

## 项目结构

- [apps/console](apps/console)：控制台
- [apps/network-gateway](apps/network-gateway)：前置网络出口约定
- [apps/register-runner](apps/register-runner)：执行器模块说明
- [apps/token-sink](apps/token-sink)：结果落池说明
- [apps/worker-runtime](apps/worker-runtime)：运行时环境定义
- [deploy](deploy)：启动脚本和部署骨架
- [.env.example](.env.example)：一体化部署环境变量模板
- [docs](docs)：架构、流程、快速开始、配置说明
- [DrissionPage_example.py](DrissionPage_example.py)：当前主执行脚本
- [email_register.py](email_register.py)：临时邮箱 provider factory 与适配层
- [mail_providers.py](mail_providers.py)：`MailProvider` 抽象基类和 6 个具体实现
- [diagnose.py](diagnose.py)：独立邮箱全链路诊断脚本

## 兼容性说明

- 根目录命令行脚本继续保留，可直接使用
- 新增控制台和模块目录不会接管你现有生产目录
- 控制台任务全部运行在 `apps/console/runtime/tasks/` 下的独立目录里

## 致谢

- 感谢 [ReinerBRO](https://github.com/ReinerBRO) 对仓库整理、部署验证和整合方向的推动。
- 感谢 [XeanYu](https://github.com/XeanYu) 和 [chenyme](https://github.com/chenyme) 的开源项目与思路，这个仓库是在他们相关工作的基础上继续整理、集成和工程化。
- [kevinr229/grok-maintainer](https://github.com/kevinr229/grok-maintainer)
- [DrissionPage](https://github.com/g1879/DrissionPage)
- [grok2api](https://github.com/chenyme/grok2api)
