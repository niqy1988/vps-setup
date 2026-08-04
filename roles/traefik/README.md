# traefik 角色

以 rootless Quadlet 容器部署 [Traefik](https://traefik.io/) 反向代理，
并配置 ACME 证书（Cloudflare DNS Challenge）、HTTP→HTTPS 重定向、
Dashboard 基本认证、日志轮转与 Cloudflare DNS 记录。

## 功能概述

1. 创建配置目录结构（`config`、`config/config.d`、`certs`、`log`、
   `log/old`）。
2. 部署 SELinux 自定义策略模块 `traefik_container.cil`（由
   `udica` 模板生成），并通过 handler `semodule -i` 安装——容器以
   `label=type:traefik_container.process` 受限运行。
3. 渲染 `traefik.yaml`（入口点、TLS、ACME resolver、Dashboard、ping）
   与 `traefik_auth.yaml`（Dashboard 基本认证中间件）。
4. 用 `containers.podman.podman_container` 生成 Quadlet 定义：
   - 镜像 `docker.io/library/traefik:<version>`，网络挂到
     `podman_network.network`；
   - 发布 `80:80` / `443:443`，挂载 config / log / certs，并复用
     `podman.sock`；
   - 注入 `CF_DNS_API_TOKEN` 环境变量供 DNS Challenge 使用；
   - `io.containers.autoupdate: registry`（自动更新）；
   - 通过容器 label 暴露 Traefik 自身 Dashboard 路由并挂上
     `traefik-auth@file` 认证中间件。
5. 启用并启动容器；在 firewalld 中开放 `http` / `https`。
6. 部署 logrotate 配置；若配置了 `cloudflare_dns_api_token`，为每个
   `domains` 创建 `traefik.<domain>` 的 CNAME 记录（Cloudflare 托管
   DNS）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `traefik_container` | str | 否 | `traefik` | Traefik 容器名 |
| `traefik_path` | str | 否 | `/app/traefik` | 宿主机配置目录 |
| `traefik_version` | str | 否 | `latest` | Traefik 镜像版本 |
| `podman_network` | str | 否 | `podman_network` | 共享的 Podman 网络名 |
| `domains` | list\[str\] | 否 | `[]` | ACME 证书域名列表 |
| `acme_email` | str | 否 | `""` | ACME 证书邮箱 |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API Token（DNS Challenge 与 DNS 记录） |
| `traefik_users` | list\[dict\] | 否 | `[]` | Dashboard 基本认证用户，格式 `{username, password}`；为空则无认证 |

## 依赖项

- **其他 role**：依赖 [`podman`](../podman/README.md) 角色（见
  `meta/main.yaml`），自动创建 Podman 用户、网络与 Quadlet 环境。
- **Ansible 变量 / facts**：
  - `podman_username` / `podman_uid`：由 `podman` role 提供（可经
    inventory 覆盖，示例见 `sample_inventory/`），用于容器目录属主与
    `podman.sock` 路径。
  - `domains` / `acme_email` / `cloudflare_dns_api_token` /
    `traefik_users`：在 inventory 中设置
    （示例见 `sample_inventory/group_vars/all/www.yaml`）。
  - 自定义 Jinja2 filter `service_rule`（`filter_plugins/traefik_filters.py`），
    用于生成多域名 Host 匹配规则。
- **前置条件**：`bootstrap.yaml` 已安装 SELinux 工具（`udica`）、
  firewalld，并创建 `/app`。

## 参数与 defaults 对照

`argument_specs` 中所有 optional 变量均已在 `defaults/main.yaml` 定义 ✅。

## 使用范例

```yaml
- hosts: xray
  roles:
    - role: traefik
      traefik_container: traefik
      traefik_path: /app/traefik
      podman_network: podman_network
      domains:
        - example.com
      acme_email: admin@example.com
      cloudflare_dns_api_token: "<cf_dns_api_token>"
      traefik_users:
        - username: admin
          password: "secret"
```

不启用认证（Dashboard 公开）时省略 `traefik_users` 即可。

作为其他角色的依赖：`xray` 在 `meta/main.yaml` 中声明
`dependencies: - role: traefik`，运行 `xray` 角色时会先自动部署 Traefik。
