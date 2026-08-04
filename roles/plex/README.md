# plex 角色

以 rootless Quadlet 容器部署 [Plex Media Server](https://www.plex.tv/)（
`docker.io/plexinc/pms-docker`），读取云端媒体库（rclone 挂载的
`<mount>/Media`）提供流媒体服务。替代旧的 `legacy_roles/_plex`（nginx 反代 +
命令式容器）实现。

## 功能概述

本角色会：

1. 创建 `/app/plex` 下的 `config` 与 `transcode` 目录；
2. 处理媒体库根目录 `plex_media_path`（默认 `/data/Media`）：
   - 当 `plex_rclone_mount` 设置时，在挂载上确保 `<mount>/Media`
     目录存在，并把 `/data/Media` 符号链接到它（媒体库落云）；若
     `/data/Media` 已存在为**真实目录**（旧配置遗留），角色会**明确失败**
     并提示先迁移内容到云端再重跑；
   - 未设置 `plex_rclone_mount` 时退化为创建本地 `/data/Media` 目录；
3. 用 `containers.podman.podman_container` + `state: quadlet` 生成容器定义
   （rootless，`user: "0:0"` + `group_add: keep-groups`，挂载 config、
   transcode、`/data`、`/mnt/rclone`），发布 `plex_direct_port` → 容器 32400，
   经 `systemd` user 会话管理；
4. 通过 `firewall_service` 在 firewalld 开放 `plex_direct_port`（供 Plex
   客户端直连）；同时通过容器 label 声明 Traefik 路由 `plex.<domain>`（挂
   `traefik-auth@file` 中间件）提供 HTTPS 网页入口；
5. 首启时传入 `plex_claim_token` 认领服务器（`plex.tv/claim` 获取）；
6. 创建 Cloudflare DNS 记录 `plex.<domain>` CNAME（当
   `cloudflare_dns_api_token` 非空时）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `plex_container` | str | 否 | `plex` | 容器名（也用作 systemd 单元名与 Traefik 路由/服务名） |
| `plex_path` | str | 否 | `/app/plex` | Plex config 与 transcode 目录 |
| `plex_version` | str | 否 | `latest` | 镜像版本（生产环境建议在 inventory 固定版本） |
| `plex_subdomain` | str | 否 | `plex` | 路由与 DNS 记录的子域前缀（生成 `plex.<domain>`） |
| `plex_direct_port` | int | 否 | `32400` | 宿主直连端口（映射到容器 32400）并在 firewalld 开放 |
| `plex_rclone_mount` | str | 否 | `""` | 用作媒体库的 rclone 挂载名（其 `<mount>/Media` 目录被暴露为 `/data/Media`）；空则用本地目录 |
| `plex_media_path` | str | 否 | `/data/Media` | 媒体库根路径（设置 `plex_rclone_mount` 时符号链接到挂载） |
| `plex_claim_token` | str | 否 | `""` | Plex 首启认领 token（敏感，inventory 设置；空则跳过认领） |
| `podman_network` | str | 否 | `podman_network` | 容器加入的 Podman 网络（`podman` 角色共享变量） |
| `domains` | list\[str\] | 否 | `[]` | 根域名列表（用于 Host 路由，inventory 每主机设置） |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API token（为空则不建 DNS 记录） |

## 依赖项

- **其他 role**：依赖 `podman`、`traefik`、`rclone`、`firewall_service`（见
  `meta/main.yaml`；firewall_service 开放 `plex_direct_port` 的 TCP）。
- **Ansible 变量 / 前置条件**：
  - `domains`：每主机的根域名列表（示例见 `sample_inventory/`）。
  - `plex_rclone_mount`：需在 host vars 的 `rclone_mounts` 中已定义，且对应
    远端配置存在，示例见 `sample_inventory/`。
  - `plex_claim_token`：首次认领需从 `plex.tv/claim` 获取，设置到 inventory。

## 参数与 defaults 对照

`argument_specs` 中所有顶层 optional 变量均已在 `defaults/main.yaml`
定义 ✅。`plex_rclone_mount` / `plex_claim_token` 默认 `""`（空则不链接云
媒体库 / 不认领）。`domains` / `cloudflare_dns_api_token` / `podman_network`
为跨 role 共享变量（行尾 `noqa` 豁免前缀检查）。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: plex
      plex_subdomain: plex
      plex_direct_port: 32400
      plex_rclone_mount: mydrive
      plex_claim_token: "<plex_claim_token>"
```

部署后：Web 界面 `https://plex.example.com`（经 Traefik，basic auth）或
`http://<host>:32400`（直连）。首次使用需在界面添加媒体库，指向
`/data/Media/TV`、`/data/Media/Movies` 等。

## 注意事项

- **媒体库在 FUSE 挂载上 inotify 不生效**：Plex 无法靠文件监听即时发现新
  片，请在设置中开启「定时扫描」（periodic scan）；rclone 的 pcloud 后端
  支持 change notification，目录列表会及时刷新，但 Plex 侧的自动扫描仍需
  定时触发。
- **认领**：`plex_claim_token` 只在首次认领时使用，之后可留空。
- **直连 vs 反代**：Plex 客户端可通过直连端口（`plex_direct_port`）或
  HTTPS 子域连接；两者入口均可用。
