# qbittorrent 角色

以 rootless Quadlet 容器部署 [qBittorrent](https://www.qbittorrent.org/)（
`lscr.io/linuxserver/qbittorrent`），作为下载客户端。下载数据**落在本地真实盘**
（不经过 rclone VFS 挂载），由 Sonarr / Radarr 完成后导入云端媒体库。

## 功能概述

本角色会：

1. 创建 `/app/qbittorrent`（配置目录）与下载目录
   `qbittorrent_download_path`（默认 `/data/Downloads`，本地真实盘）；
2. 在**首次启动前**播种 `qBittorrent.conf`（监听端口、WebUI 端口/账号、
   反代所需 `HostHeaderValidation/CSRFProtection` 关闭、PBKDF2 密码哈希）
   与 `categories.json`（按 `qbittorrent_categories` 预置分类与保存路径）；
   qBittorrent 首次启动后自行接管配置（角色不再改动，保证幂等）；
3. 用 `containers.podman.podman_container` + `state: quadlet` 生成容器定义
   （rootless，`user: "0:0"` + `group_add: keep-groups`，挂载
   `{{ qbittorrent_path }}:/config` 与下载目录），发布 BT 监听端口
   `qbittorrent_direct_port` 的 TCP/UDP，经 `systemd` user 会话管理；
4. 通过 `firewall_service` 在 firewalld 开放 BT 端口（TCP+UDP）；
5. 通过容器 label 声明 Traefik 路由 `bt.<domain>`（挂 `traefik-auth@file`
   中间件）到 WebUI 端口，WebUI 不直接对外发布端口；
6. 创建 Cloudflare DNS 记录 `bt.<domain>` CNAME（当
   `cloudflare_dns_api_token` 非空时）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `qbittorrent_container` | str | 否 | `qbittorrent` | 容器名（也用作 systemd 单元名与 Traefik 路由/服务名） |
| `qbittorrent_path` | str | 否 | `/app/qbittorrent` | 配置目录（挂载为容器 `/config`） |
| `qbittorrent_version` | str | 否 | `latest` | 镜像版本（生产环境建议在 inventory 固定版本） |
| `qbittorrent_subdomain` | str | 否 | `bt` | 路由与 DNS 记录的子域前缀（生成 `bt.<domain>`） |
| `qbittorrent_webui_port` | int | 否 | `8080` | 容器 WebUI 端口（不发布，走 Traefik） |
| `qbittorrent_webui_username` | str | 否 | `admin` | WebUI 用户名（Sonarr/Radarr 也用它作为 API 凭据） |
| `qbittorrent_webui_password` | str | 否 | `""` | WebUI 密码（敏感，inventory 设置；空则跳过播种，qBittorrent 首启随机生成并写日志） |
| `qbittorrent_direct_port` | int | 否 | `6881` | BT 监听端口（TCP+UDP，发布到宿主并开放 firewalld） |
| `qbittorrent_download_path` | str | 否 | `/data/Downloads` | 本地下载目录（真实盘，勿指向 rclone 挂载） |
| `qbittorrent_categories` | list\[dict\] | 否 | `[]` | 首启预置的分类（`name` + `save_path`，须与 Sonarr/Radarr 的分类一致） |
| `podman_network` | str | 否 | `podman_network` | 容器加入的 Podman 网络（`podman` 角色共享变量） |
| `domains` | list\[str\] | 否 | `[]` | 根域名列表（用于 Host 路由，inventory 每主机设置） |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API token（为空则不建 DNS 记录） |

## 依赖项

- **其他 role**：依赖 `podman`、`traefik`、`firewall_service`（见
  `meta/main.yaml`；firewall_service 开放 `qbittorrent_direct_port` 的
  TCP/UDP）。不依赖 `rclone`——下载走本地真实盘，与挂载解耦。
- **Ansible 变量 / 前置条件**：
  - `domains`：每主机的根域名列表（示例见 `sample_inventory/`）。
  - `qbittorrent_webui_password`：建议在 inventory 设置（否则首启密码随机）。
  - `qbittorrent_categories` 中每个 `save_path` 建议位于
    `qbittorrent_download_path` 下，且与 Sonarr/Radarr 下载客户端配置的分类一致。

## 参数与 defaults 对照

`argument_specs` 中所有顶层 optional 变量均已在 `defaults/main.yaml`
定义 ✅。`qbittorrent_webui_password` 默认 `""`（有意不设默认，敏感值放
inventory）。`domains` / `cloudflare_dns_api_token` / `podman_network` 为跨
role 共享变量（行尾 `noqa` 豁免前缀检查）。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: qbittorrent
      qbittorrent_subdomain: bt
      qbittorrent_direct_port: 6881
      qbittorrent_categories:
        - name: sonarr
          save_path: /data/Downloads/sonarr
        - name: radarr
          save_path: /data/Downloads/radarr
```

部署后：Web 界面 `https://bt.example.com`（经 Traefik，先 basic auth 后
qBittorrent 登录，即双认证；如需单认证可去掉 `traefik-auth@file` label）。

## 注意事项

- **配置首启播种**：`qBittorrent.conf` / `categories.json` 只在首次部署时写入
  （stat 判断），之后由 qBittorrent 自行管理，角色不覆盖 → 幂等。若需改动
  WebUI 密码/分类，可先在 WebUI 修改，或删除容器配置后重跑本角色。
- **BT 端口与 rootless UDP**：rootless Podman 发布 UDP 端口的可靠性取决于
  网络后端（slirp4netns/pasta）；TCP 一般可靠。若实测 uTP/DHT 不可用，
  可评估改用 host 网络模式（WebUI 绑 `127.0.0.1`）。
- **密码哈希**：角色用内置 filter 生成与 qBittorrent 一致的
  PBKDF2-HMAC-SHA512（100000 次迭代，salt16 + dk64）哈希写入配置。
