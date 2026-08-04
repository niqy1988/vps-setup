# VPS-Setup Context

## Glossary

### Traefik
HTTPS 入口路由器，终结 TLS。使用 ACME + Cloudflare DNS challenge 管理证书。部署为 Podman Quadlet 容器，运行在 `podman_network` 中。通过容器 labels（`traefik.http.*`）自动发现后端服务——路由规则定义在各自容器的 `.container` Quadlet 文件中（container-defined routing）。不生成 `traefik_dynamic.yml`。关闭 buffering，开启 streaming，支持 WebSocket 长连接不超时。无 Nginx 兜底——未匹配路径由 Traefik 默认返回 404。

### container-defined routing
每个容器的 Quadlet `.container` 文件中直接包含 `traefik.http.routers.*` 和 `traefik.http.services.*` labels，Traefik 读取后自动注册路由。与"全局路由配置"相对，新容器只需自带 labels 即可接入。

### Xray
VLESS 代理后端，支持 WebSocket 和 XHTTP 两种传输层协议。不做 TLS 终结，接收来自 Traefik 的 HTTP 流量。使用 host 网络模式以保留 UDP/QUIC 兼容性。容器内进程以 root (0:0) 运行。Xray 自行处理 `/xray/proxy*` 子路径的协议分流（WS vs xHTTP），Traefik 只识别 `/xray/proxy` 前缀。保留 routing 段落用于未来 wgcf 出站路由。Quadlet 定义中配置健康检查（systemd 生命周期管理），Traefik 通过 stats API 端口（由 `xray_stats_port` 变量配置）做路由层健康检查。

### Quadlet
Podman 的声明式 systemd 容器定义文件格式（`.container`, `.network`, `.volume`），替代命令式 `podman_container` Ansible 模块。定义文件以 J2 模板存放在角色 `templates/quadlet/` 下，Ansible 渲染后部署到 `~/.config/containers/systemd/`，通过 systemd 管理生命周期。

### podman_network
自定义 Podman 容器网络，由 Quadlet `.network` 文件定义。Traefik 加入此网络，Xray 通过 host 网络模式通过 `127.0.0.1` 访问 podman_network 中的服务。网络定义在 `podman` role 内创建。

### rootless
容器以非 root 用户（`podman_username`）创建和管理，但容器内进程可以以 root 运行。区别：rootless 指的是容器运行时，不是容器内进程权限。

### 服务发现
Traefik 通过 Docker/ Podman provider 读取容器标签（`traefik.http.*`）自动注册后端服务，不使用静态动态配置文件。

### fallback
Xray 处理无法识别的流量时转发到其他目的地的机制。在当前架构中，Traefik 负责路由，Xray 不再需要 fallback 到 Traefix。

### playbook
Ansible 按主机组部署的 YAML 文件，位于 `playbooks/` 下（如 `all.yaml`、`xray.yaml`）。定义目标主机组运行的角色列表和执行顺序；已无 per-host playbook。

### role
Ansible 的可复用角色，包含 tasks、handlers、templates、defaults、meta 等目录。如 `traefik/`, `xray/`, `podman/`。argument_specs.yaml 声明角色所需的外部变量。

### bootstrap
初始化所有 VPS 基础环境的 playbook（`bootstrap.yaml`），包括 SSH 密钥登录、firewalld、BBR、/app 和 /data 目录等。

### SSH 认证
Ansible 全链路不指定 private key file。连接时认证交给 OpenSSH 自动发现密钥：优先使用本地 ssh agent 中已加载的密钥，也会自动尝试默认位置的私钥（如 `~/.ssh/id_ed25519`），无需（也不强制）依赖 ssh agent。公钥通过 `user` 角色以文本形式（`ssh_public_key`）部署到被管理机器的 authorized_keys。

## Host Groups

| Group | Purpose |
|-------|---------|
| `prod` | 生产机，podman镜像指定版本，SELinux enforcing，默认不允许交互式用户登录 |
| `dev` | 开发机，podman镜像选择latest，SELinux permissive，允许交互式用户登录的主机 |
| `interactive` | 允许交互式用户登录的生产机 |
| `xray` | 部署 Xray 代理服务的主机 |

## Service Deployment Matrix (xray hosts)

适用于 `xray` 组全部主机，由 `playbooks/xray.yaml`（经 `all.yaml` 引入）统一部署。该架构最初在单台主机落地，现已全面铺开。

| Service | Role | Network | TLS | Service Discovery |
|---------|------|---------|-----|-------------------|
| Podman (rootless) | `podman` | — | — | — |
| Traefik | `traefik` | `podman_network` (Quadlet) | Yes (ACME) | Labels (self-defined routes) |
| Xray | `xray` | `host` | No (HTTP only) | Labels in .container Quadlet; backend at `127.0.0.1`（Xray 入站端口，见 `sample_inventory/`）|

## Architectural Decisions Summary

| # | Decision | Key Detail |
|---|----------|------------|
| 1 | Nginx role removed project-wide | _nginx role deleted; not used on any xray host |
| 2 | Traefik ACME replaces acme.sh | Certificates managed by Traefik; acme role removed |
| 3 | Xray host network mode | UDP/QUIC compatibility |
| 4 | Traefik routes to Xray | Not reverse fallback |
| 5 | Route matching = PathPrefix only | Traefik only matches `/xray/proxy*`, Xray handles sub-path splitting |
| 6 | Xray no TLS termination | HTTP-only backend, Traefik handles TLS |
| 7 | Quadlet definitions as J2 templates | Ansible renders variables |
| 13 | Xray supports ws + xhttp | Single entry port（由 `xray_*_port` 变量配置）; Xray handles sub-path protocol splitting |
| 8 | Templates in subdirectories | templates/quadlet/ and templates/config/ |
| 9 | podman_network in podman role | Shared infrastructure |
| 10 | systemd reload via handlers | Per-role handler triggers |
| 11 | Xray process runs as root in container | Container itself is rootless |
| 12 | argument_specs as primary docs | defaults/main.yaml for fallback defaults |
| 14 | wgcf routing reserved | Details deferred |
| 15 | xray hosts: podman + traefik + xray only | nginx removed |
| 16 | Firewall opened in traefik role handler | Port 80/443 after config deployed |
| 17 | Cloudflare token via env var | From www.yaml, no vault needed yet |
| 18 | Label-based service discovery | No traefik_dynamic.yml; routes in container .container Quadlet labels |
| 19 | Traefik traefik.toml simplified | Only entrypoints, providers, ACME, buffering/streaming config |
| 20 | Xray routing section kept | Future wgcf rules to be added |
| 21 | Single entry port for WS + xHTTP | 由 `xray_*_port` 变量配置; Xray handles sub-path protocol splitting, not Traefik |
| 22 | No Nginx on any xray host | _nginx role removed project-wide |
| 23 | Container-defined routing | Each container's .container Quadlet has its own traefik.http.* labels |
| 24 | Double health check | Quadlet healthcheck (systemd) + Traefik HTTP probe to Xray stats API |
| 25 | Xray host network address | Traefik routes to `127.0.0.1`（Xray 入站端口，见 `sample_inventory/`）for Xray backend |

## Removed Roles & Cleanup Log (2026-08-04)

### Deleted
- `roles/_acme/` — acme.sh 证书管理，已被 Traefik ACME 取代
- `roles/_nginx/` — nginx 反向代理，已被 Traefik 取代
- 模板：`roles/plex/templates/plex.conf.j2`、`roles/qbittorrent/templates/qbittorrent.conf.j2`、`roles/filebrowser/templates/filebrowser.conf.j2`

### Reference cleanup (by role / playbook)
- `roles/plex/`：meta 移除 `nginx` 依赖；tasks 删除 "Create nginx rule" 任务；handlers 删除 `Reload nginx` notify
- `roles/qbittorrent/`：meta 移除 `nginx` 依赖；tasks 删除 "Create nginx rule" 任务
- `roles/filebrowser/`：defaults 删除自引用 `nginx_path`/`nginx_user`；tasks 删除 nginx site rules 段
- `tests/`：`file_server.yaml`、`hath.yaml`、`media_server.yaml`、`seedbox.yaml`、`wordpress.yaml` 移除 `docker` 与 `nginx` 的 role play
- `docs/CONTEXT.md`：决策 #1/#2/#15/#22 更新
- `docs/adr/0002-traefik-acme.md`：consequence 更新（acme role 已删除）

### Known leftover issues
- `tests/` 整体已与当前项目脱节，仍引用不存在的 role：`certbot`、`mysql`、`wordpress`、`www`、`hath`（旧 `rclone` 引用已由正式 `roles/rclone/` 取代，tests 引用待清理）

### TODO
- [ ] `filebrowser`/`plex`/`qbittorrent` 对外访问改由 Traefik 容器标签（`traefik.http.*`）+ Podman 完成，替代旧 nginx 反代（参照 `xray`/`traefik` 的 Quadlet labels 做法）
- [ ] 清理/重写 `tests/` 目录，删除或迁移引用已不存在 role 的测试场景

