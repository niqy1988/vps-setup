# filebrowser 角色

以 rootless Quadlet 容器部署 [filebrowser](https://filebrowser.org/)（社区
fork `ghcr.io/gtsteffaniak/filebrowser`，YAML 配置），通过 Traefik 提供
Web 文件管理与 WebDAV 访问。

## 功能概述

本角色会：

1. 创建 `/app/filebrowser`（`database.db`、`cache`、`log` 与
   `config.yaml`）；
2. 依赖 `rclone` 角色部署挂载（完整配置见 host vars 的共享变量
   `rclone_mounts`），并为 `filebrowser_rclone_mounts` 中的每个名字在
   `/data/<name>` 创建指向 `/mnt/rclone/<name>` 的符号链接，作为
   filebrowser 的数据源暴露（`/data` 即 `sources` 中的 `Data` 根）；
3. 用 `containers.podman.podman_container` + `state: quadlet` 生成容器
   定义（rootless，`user: "0:0"` + `group_add: keep-groups`，挂载
   `/data` 与 `/mnt/rclone:rshared`），挂到 `podman_network`，经
   `systemd` user 会话管理生命周期；
4. 通过容器 label 声明 Traefik 路由：
   - 主路由：`file.<domain>`，挂 `traefik-auth@file` 中间件（basic auth
     统一认证，认证信息由 `traefik` 角色管理）；
   - WebDAV 路由：`file.<domain>/dav/<source>/`（源名见 config 的
     `server.sources`），**不挂** traefik-auth（WebDAV 走 filebrowser
     自带 Basic Auth：用户名 + JWT token）；
5. 创建 Cloudflare DNS 记录 `file.<domain>` CNAME（当
   `cloudflare_dns_api_token` 非空时）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `filebrowser_container` | str | 否 | `filebrowser` | 容器名（也用作 systemd 单元名与 Traefik 路由/服务名） |
| `filebrowser_path` | str | 否 | `/app/filebrowser` | 配置与数据目录 |
| `filebrowser_version` | str | 否 | `latest` | 镜像版本（生产环境建议在 inventory 固定版本） |
| `filebrowser_subdomain` | str | 否 | `file` | 路由与 DNS 记录的子域前缀（生成 `file.<domain>`） |
| `filebrowser_rclone_mounts` | list\[str\] | 否 | `[]` | 要暴露到 `/data` 下的 rclone 挂载名称列表（完整配置见 host vars 的 `rclone_mounts`） |
| `podman_network` | str | 否 | `podman_network` | 容器加入的 Podman 网络（`podman` 角色共享变量） |
| `domains` | list\[str\] | 否 | `[]` | 根域名列表（用于 Host 路由，inventory 每主机设置） |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API token（为空则不建 DNS 记录） |

## 依赖项

- **其他 role**：依赖 `podman`、`traefik`、`rclone`（见 `meta/main.yaml`）。
  `rclone` 角色直接读取 host vars 的同名共享变量 `rclone_mounts`（挂载
  完整配置的唯一入口），本角色不覆盖、不过滤；`filebrowser_rclone_mounts`
  仅用于本角色在 `/data` 下建符号链接：
  ```yaml
  dependencies:
    - role: podman
    - role: traefik
    - role: rclone
  ```
  `traefik` 提供 `traefik-auth@file` 中间件与路由；`podman` 提供 rootless
  环境、网络与用户。
- **Ansible 变量 / 前置条件**：
  - `domains`：每主机的根域名列表（示例见 `sample_inventory/`）。
  - `cloudflare_dns_api_token`：为空则跳过 DNS 记录（示例见
    `sample_inventory/`）。
  - `filebrowser_rclone_mounts` 中的每个名字需在 host vars 的 `rclone_mounts`
    中定义（含 `vfs_cache_*` 等配置），且对应的 rclone 远端配置
    （`rclone_conf_src_dir` 下的 `<name>.conf`）需存在，示例见
    `sample_inventory/`。

## 参数与 defaults 对照

`argument_specs` 中所有顶层 optional 变量均已在 `defaults/main.yaml`
定义 ✅。`filebrowser_rclone_mounts` 默认 `[]`（空则只部署容器、不建
符号链接），实际值在 inventory 设置。`domains` / `cloudflare_dns_api_token`
/ `podman_network` 为跨 role 共享变量（行尾 `noqa` 豁免前缀检查）。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: filebrowser
      filebrowser_subdomain: file
      filebrowser_rclone_mounts:
        - mydrive
```

`mydrive` 的完整挂载配置（`vfs_cache_mode` 等）在 host vars 的
`rclone_mounts` 中定义。

部署后：Web 管理界面 `https://file.example.com`（需 traefik basic auth）；
WebDAV `https://file.example.com/dav/<source>/`（如 `/dav/Data/`，用
filebrowser Basic Auth：用户名 + JWT token 当密码）。
