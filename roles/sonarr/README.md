# sonarr 角色

以 rootless Quadlet 容器部署 [Sonarr](https://sonarr.tv/)（
`lscr.io/linuxserver/sonarr`），用于管理剧集媒体库与下载导入。媒体库位于
rclone 挂载（`<mount>/Media`），由 Plex 等读取。

## 功能概述

本角色会：

1. 创建 `/app/sonarr`（配置目录）；
2. 处理媒体库根目录 `sonarr_media_path`（默认 `/data/Media`）：
   - 当 `sonarr_rclone_mount` 设置时，在挂载上确保 `<mount>/Media`
     目录存在，并把 `/data/Media` 符号链接到它（媒体库落云，供 Plex 读取）；
     若 `/data/Media` 已存在为**真实目录**（旧配置遗留），角色会**明确失败**
     并提示先迁移内容到云端再重跑（避免静默走本地路径）；
   - 未设置 `sonarr_rclone_mount` 时退化为创建本地 `/data/Media` 目录；
3. 用 `containers.podman.podman_container` + `state: quadlet` 生成容器定义
   （rootless，`user: "0:0"` + `group_add: keep-groups`，挂载
   `{{ sonarr_path }}:/config`、`/data`、`/mnt/rclone`），挂到
   `podman_network`，经 `systemd` user 会话管理；
4. 通过容器 label 声明 Traefik 路由 `sonarr.<domain>`（挂
   `traefik-auth@file` 中间件），Web 端口不直接发布；
5. 创建 Cloudflare DNS 记录 `sonarr.<domain>` CNAME（当
   `cloudflare_dns_api_token` 非空时）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `sonarr_container` | str | 否 | `sonarr` | 容器名（也用作 systemd 单元名与 Traefik 路由/服务名） |
| `sonarr_path` | str | 否 | `/app/sonarr` | 配置与数据目录 |
| `sonarr_version` | str | 否 | `latest` | 镜像版本（生产环境建议在 inventory 固定版本） |
| `sonarr_subdomain` | str | 否 | `sonarr` | 路由与 DNS 记录的子域前缀（生成 `sonarr.<domain>`） |
| `sonarr_port` | int | 否 | `8989` | 容器 Web 端口（不发布，走 Traefik） |
| `sonarr_rclone_mount` | str | 否 | `""` | 用作媒体库的 rclone 挂载名（其 `<mount>/Media` 目录被暴露为 `/data/Media`）；空则用本地目录 |
| `sonarr_media_path` | str | 否 | `/data/Media` | 媒体库根路径（设置 `sonarr_rclone_mount` 时符号链接到挂载） |
| `podman_network` | str | 否 | `podman_network` | 容器加入的 Podman 网络（`podman` 角色共享变量） |
| `domains` | list\[str\] | 否 | `[]` | 根域名列表（用于 Host 路由，inventory 每主机设置） |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API token（为空则不建 DNS 记录） |

## 依赖项

- **其他 role**：依赖 `podman`、`traefik`、`rclone`（见 `meta/main.yaml`）。
  `rclone` 角色部署挂载（完整配置见 host vars 的共享变量 `rclone_mounts`），
  `sonarr_rclone_mount` 中的名字需在 `rclone_mounts` 中定义。
- **Ansible 变量 / 前置条件**：
  - `domains`：每主机的根域名列表（示例见 `sample_inventory/`）。
  - `sonarr_rclone_mount`：需在 host vars 的 `rclone_mounts` 中已定义，且对应
    远端配置（`rclone_conf_src_dir` 下的 `<name>.conf`）存在，示例见
    `sample_inventory/`。
  - 下载目录（如 `/data/Downloads`）由 `qbittorrent` 角色创建并挂载进容器，
    Sonarr 通过 `/data` 路径可见同一目录。

## 参数与 defaults 对照

`argument_specs` 中所有顶层 optional 变量均已在 `defaults/main.yaml`
定义 ✅。`sonarr_rclone_mount` 默认 `""`（空则不链接云媒体库）。
`domains` / `cloudflare_dns_api_token` / `podman_network` 为跨 role 共享变量
（行尾 `noqa` 豁免前缀检查）。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: sonarr
      sonarr_subdomain: sonarr
      sonarr_rclone_mount: mydrive
```

部署后：Web 界面 `https://sonarr.example.com`（经 Traefik，basic auth）。
首次使用需在界面配置：下载客户端（qBittorrent，地址 `http://qbittorrent:8080`）、
根目录 `/data/Media/TV`、质量与索引器等。
