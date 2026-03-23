# Grok Register

面向 `x.ai` 注册批处理的一体化项目。

这个仓库现在不是单一脚本仓库，而是一个“统一项目、内部解耦”的闭环方案，包含：

- `network`：WARP / 代理桥接
- `register`：注册执行器
- `sink`：把成功结果推到 `grok2api` 等下游
- `console`：任务创建、状态监控、日志查看
- `worker-runtime`：`Xvfb + Chrome/Chromium + Python` 运行环境定义

## 你能直接用它做什么

- 命令行直接跑注册
- 在 Web 控制台里创建批量任务
- 给每个任务独立配置出口、邮箱参数和 sink
- 实时查看每个任务的轮次、成功数、失败数和日志
- 注册成功后自动把 `sso` 推入 `grok2api` 兼容接口

## 项目结构

- [apps/console](apps/console)：控制台
- [apps/network-gateway](apps/network-gateway)：前置网络出口约定
- [apps/register-runner](apps/register-runner)：执行器模块说明
- [apps/token-sink](apps/token-sink)：结果落池说明
- [apps/worker-runtime](apps/worker-runtime)：运行时环境定义
- [deploy](deploy)：启动脚本和部署骨架
- [docs](docs)：架构、流程、快速开始、配置说明
- [DrissionPage_example.py](DrissionPage_example.py)：当前主执行脚本
- [email_register.py](email_register.py)：临时邮箱适配层

## 快速入口

- 新手先看 [docs/quickstart.md](docs/quickstart.md)
- 想看完整链路看 [docs/business-flow.md](docs/business-flow.md)
- 想弄清楚字段含义看 [docs/options.md](docs/options.md)
- 想看模块边界看 [docs/architecture.md](docs/architecture.md)

## 命令行运行

```bash
cd /home/codex/grok-register
cp config.example.json config.json
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python DrissionPage_example.py --count 1
```

## 控制台运行

```bash
cd /home/codex/grok-register
./deploy/start-console.sh
```

默认监听 `0.0.0.0:18600`。

## Docker 一键部署

如果你更希望直接用容器启动控制台，可以在仓库根目录执行：

```bash
git clone git@github.com:509992828/grok-register.git
cd grok-register
docker compose up -d --build
```

启动后访问：

- `http://<你的服务器IP>:18600`

这个 Compose 会完成下面几件事：

- 构建带 `Xvfb + Chrome + Python` 的运行镜像
- 启动 Web 控制台
- 让控制台里的任务直接复用容器内的浏览器和 Python 运行环境

注意：

- Docker 只能帮你把项目启动起来，不能替你提供可用的 WARP 出口、临时邮箱服务和 grok2api sink
- 第一次启动前，你仍然需要在控制台里填好这些业务参数

## 当前配置模板

```json
{
  "run": {
    "count": 50
  },
  "temp_mail_api_base": "https://mail-api.example.com",
  "temp_mail_admin_password": "<your_admin_password>",
  "temp_mail_domain": "mail.example.com",
  "temp_mail_site_password": "",
  "proxy": "",
  "browser_proxy": "",
  "api": {
    "endpoint": "http://127.0.0.1:18000/api/v1/admin/tokens",
    "token": "",
    "append": true
  }
}
```

配置模板说明：

- 仓库里提供的是可公开分享的示例配置，不包含任何真实邮箱接口、真实域名、密码或 token
- 实际运行时，请把你自己的参数写进本机 `config.json` 或控制台系统配置里，不要把生产凭据提交回仓库
- 代码兼容旧版 `duckmail_*` 字段，只是为了照顾历史配置；第一次部署的新用户，直接使用 `temp_mail_*` 这一套字段即可

## 闭环要求

只有下面 4 段都通，业务才算真正能跑批：

1. 网络出口通：`browser_proxy` / `proxy`
2. 临时邮箱通：`temp_mail_api_base` / `temp_mail_domain`
3. 注册执行通：浏览器、`Xvfb`、Python 依赖齐全
4. sink 通：`api.endpoint` / `api.token`

## 兼容性说明

- 根目录命令行脚本继续保留，可直接使用
- 新增控制台和模块目录不会接管你现有生产目录
- 控制台任务全部运行在 `apps/console/runtime/tasks/` 下的独立目录里

## 致谢

- 感谢 [XeanYu](https://github.com/XeanYu) 和 [chenyme](https://github.com/chenyme) 的开源项目与思路，这个仓库是在他们相关工作的基础上继续整理、集成和工程化。
- [kevinr229/grok-maintainer](https://github.com/kevinr229/grok-maintainer)
- [DrissionPage](https://github.com/g1879/DrissionPage)
- [grok2api](https://github.com/chenyme/grok2api)
