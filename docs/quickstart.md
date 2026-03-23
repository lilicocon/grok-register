# 快速开始

## 1. 准备基础环境

如果你是第一次接触这个项目，先记住一件事：

这个项目不是“拉下来直接点运行就能注册成功”的类型。它依赖 3 个外部条件：

- 可用的网络出口，例如 WARP / 代理桥接
- 可被 `x.ai` 接受的临时邮箱域名
- 可接收 token 的下游 sink，例如 `grok2api`

只有这 3 段都准备好，项目才会真正跑通。

宿主机模式下，至少准备好：

- Python 3.10+
- 根目录虚拟环境 `.venv`
- Chrome/Chromium
- `Xvfb`
- 可用的 WARP / 代理桥接
- 一个可用的临时邮箱 API
- 一个可写入的 `grok2api` 兼容 sink

## 2. 安装依赖

```bash
cd /home/codex/grok-register
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb
```

## 3. Docker 一键启动控制台

如果你不想先在宿主机手工装一堆依赖，可以直接用 Docker：

```bash
git clone https://github.com/509992828/grok-register.git
cd grok-register
docker compose up -d --build
```

默认端口：

- `18600`

启动后打开：

- `http://<你的服务器IP>:18600`

说明：

- 这个 Compose 会把控制台、浏览器和 Python 运行环境一起起起来
- 但它不会自动替你部署 WARP、临时邮箱 API、grok2api
- 这些仍然需要你自己准备，然后填到控制台里

## 4. 准备运行配置

```bash
cp config.example.json config.json
```

把下面这些替换成你自己的值：

- `temp_mail_api_base`
- `temp_mail_admin_password`
- `temp_mail_domain`
- `browser_proxy`
- `proxy`
- `api.endpoint`
- `api.token`

## 5. 先做一次命令行验证

```bash
cd /home/codex/grok-register
. .venv/bin/activate
python DrissionPage_example.py --count 1
```

只要这一步能成功产出 `sso/*.txt`，说明注册执行链路已经基本通了。

## 6. 宿主机方式启动控制台

```bash
cd /home/codex/grok-register
./deploy/start-console.sh
```

默认监听：

- `0.0.0.0:18600`

如果只想本机访问：

```bash
GROK_REGISTER_CONSOLE_HOST=127.0.0.1 ./deploy/start-console.sh
```

## 7. 在控制台里开始跑业务

推荐做法：

1. 先在“系统默认配置”里填好稳定参数
2. 保存后，新建一个 `count=1` 的验证任务
3. 确认日志、邮箱、token 入池都正常
4. 再创建真正的批量任务，例如 `count=50`

## 8. 成功后你会看到什么

- 任务目录：`apps/console/runtime/tasks/task_<id>/`
- 控制台日志：`apps/console/runtime/tasks/task_<id>/console.log`
- 本地 token 文件：`apps/console/runtime/tasks/task_<id>/sso/task_<id>.txt`
- 主脚本日志：`apps/console/runtime/tasks/task_<id>/logs/`
