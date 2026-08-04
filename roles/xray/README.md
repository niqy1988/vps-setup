# xray 角色

以 rootless Quadlet 容器部署 [Xray](https://xtls.github.io/) 代理服务
（VLESS + WebSocket / XHTTP），并通过 Traefik 暴露路由、经 Cloudflare
托管 DNS 解析域名。

## 功能概述

1. 创建目录结构（`config`、`log`、`log/old`）。
2. 渲染 `templates/xray/*.j2` 到 `{{ xray_path }}/config/`：
   - `00_base.json`：日志、统计、API（健康检查 / 带宽统计）；
   - `30_inbound_block.json`：黑洞 fallback 入口；
   - `31_inbound_ws.json`：VLESS + WebSocket 两个入口
     （`ws`、`ws-v1`）；
   - `32_inbound_xhttp.json`：VLESS + XHTTP 两个入口
     （`xhttp-v2`、`xhttp-wg`）；
   - `50_outbound.json`：native / ipv4 / blackhole 出口；
   - `51_outbound_wgcf.json`：从 `ansible_local.wgcf.wgcf_xray_config`
     注入 WireGuard 出口（依赖 `wgcf` 角色）；
   - `70_routing.json`：路由规则（wgcf 出口 / ipv4 / native）；
   - `90_geodata.json`：geodata 定时更新。
3. 用 `containers.podman.podman_container` 生成 Quadlet 定义：
   镜像 `ghcr.io/xtls/xray-core:<version>`，挂载 config / log，网络挂到
   `podman_network.network`，`io.containers.autoupdate: registry`；
   通过容器 label 定义 Traefik 路由（按 `xray_url_path` 生成的路径前缀），
   WebSocket / XHTTP 入口端口见下文变量。
4. 启用并启动容器；部署 logrotate；若配置了
   `cloudflare_dns_api_token`，为每个 `domains` 创建 `www.<domain>`
   的 CNAME 记录。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `xray_container` | str | 否 | `xray` | Xray 容器名 |
| `xray_path` | str | 否 | `/app/xray` | 宿主机配置目录 |
| `xray_version` | str | 否 | `latest` | Xray 镜像版本 |
| `xray_stats_port` | int | 否 | `80` | Stats API 端口（健康检查 / 带宽统计） |
| `xray_url_path` | str | 否 | `/xray/proxy` | WebSocket 升级路径前缀 |
| `xray_clients` | list\[dict\] | 否 | `[]` | VLESS 客户端列表（`id`、`level`、`email`） |
| `domains` | list\[str\] | 否 | `[]` | 域名列表（Traefik 路由 + DNS 记录） |
| `cloudflare_dns_api_token` | str | 否 | `""` | Cloudflare DNS API Token（创建 `www` 记录） |

> 补充：`defaults/main.yaml` 还定义了 `argument_specs` 之外的入站端口变量
> `xray_ws_port`（81）、`xray_ws_v1_port`（82）、`xray_xhttp_v2_port`（83）、
> `xray_xhttp_wg_port`（84）。需要覆盖时在 inventory 中设置即可
> （示例见 `sample_inventory/group_vars/xray/xray.yaml`）。

## 依赖项

- **其他 role**（见 `meta/main.yaml`）：
  - [`podman`](../podman/README.md)：提供 rootless Podman 环境；
  - [`traefik`](../traefik/README.md)：提供反向代理与路由；
  - [`wgcf`](../wgcf/README.md)：注册 Cloudflare WARP 设备，产出
    WireGuard 出口配置（写进 `ansible_local.wgcf.wgcf_xray_config`）。
- **Ansible 变量 / facts**：
  - `podman_username` / `podman_uid` / `podman_network`（来自 `podman`
    role，可经 inventory 覆盖，示例见 `sample_inventory/`）；
  - `ansible_local.wgcf.wgcf_xray_config`（`wgcf` 角色写入的事实）；
  - `domains`、`cloudflare_dns_api_token`（示例见
    `sample_inventory/group_vars/all/www.yaml`）、`xray_clients`
    （示例见 `sample_inventory/group_vars/xray/credentials.yaml`）。
  - 自定义 Jinja2 filter `service_rule`（`filter_plugins/traefik_filters.py`）。

## 参数与 defaults 对照

`argument_specs` 中所有 optional 变量均已在 `defaults/main.yaml` 定义 ✅。

> 备注：`argument_specs` 中 `xray_clients` 文档默认值为 `[]`，而
> `defaults/main.yaml` 中给了一个示例条目（占位 UUID）——实际值通常
> 在 inventory 中覆盖（示例见
> `sample_inventory/group_vars/xray/credentials.yaml`）。

## 使用范例

本项目在 `playbooks/xray.yaml` 中调用：

```yaml
- name: Set up xray
  hosts: xray
  roles:
    - role: xray
```

所需变量在 inventory 中提供（各变量示例见 `sample_inventory/` 目录，
分别位于 `group_vars/all/` 与 `group_vars/xray/` 下）。

手动指定核心参数：

```yaml
- hosts: xray
  roles:
    - role: xray
      xray_path: /app/xray
      xray_container: xray
      xray_url_path: /xray/proxy
      xray_clients:
        - id: "uuid-here"
          level: 0
          email: admin@example.com
      domains:
        - example.com
```
