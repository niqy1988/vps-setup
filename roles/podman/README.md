# podman 角色

为 rootless 容器管理准备完整的 Podman 环境。本角色是本项目
`traefik` / `xray` 等容器类角色共用的基础角色。

## 功能概述

1. 安装 `podman`、`systemd-container`、`net-tools`（健康检查用）、
   `podman`（pip 包，供 `containers.podman` 集合调用）、`udica`
   （SELinux 容器策略工具）。
2. 通过 `sysctl` 将非特权端口起点设为 `80`（`net.ipv4.ip_unprivileged_port_start`），
   使 rootless 容器可绑定 80/443。
3. 为 Podman 用户创建 Quadlet 目录
   `~/.config/containers/systemd`。
4. 以 `quadlet` 模式创建默认 bridge 网络（`podman_network`，含 IPv6）。
   网络重建通过 handler `Create podman network` 触发（先删后建）。
5. 启用并启动 `podman-auto-update.service` / `podman-auto-update.timer`
   与 `podman.socket`（用户级 systemd）。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `podman_username` | str | 否 | `podman_user` | 非 root 的 Podman 用户名 |
| `podman_uid` | int | 否 | `1000000` | Podman 用户的 UID/GID |
| `podman_network` | str | 否 | `podman_network` | 默认 Podman bridge 网络名 |

> 需要覆盖默认值时，在 inventory 中设置对应变量即可
> （示例见 `sample_inventory/group_vars/all/podman.yaml`）。

## 依赖项

- **其他 role**：依赖 [`user`](../user/README.md) 角色（见
  `meta/main.yaml`），以创建 Podman 用户：
  ```yaml
  dependencies:
    - role: user
      username: "{{ podman_username }}"
      uid: "{{ podman_uid }}"
      user_groups: [systemd-journal, users]
      linger: true
      comment: podman user
  ```
  其中 `linger: true` 保证用户级 systemd 服务（Quadlet 容器）开机自启。
- **Ansible 变量 / 前置条件**：
  - 依赖 `user` 角色为 Podman 用户写入 `/etc/subuid`、`/etc/subgid`
    映射（rootless 容器 UID 映射基础）。
  - 建议先执行 `playbooks/bootstrap.yaml`（安装 SELinux 工具、
    firewalld、创建 `/app` 等）。

## 参数与 defaults 对照

`argument_specs` 中所有 optional 变量（`podman_username`、`podman_uid`、
`podman_network`）均已在 `defaults/main.yaml` 中定义 ✅。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: podman
      podman_username: podman_user
      podman_uid: 1000000
      podman_network: podman_network
```

也可仅用默认值：

```yaml
- hosts: dev
  roles:
    - role: podman
```

作为其他角色的依赖：`traefik` / `xray` 在各自 `meta/main.yaml` 中声明
`dependencies: - role: podman`，因此直接运行这两个角色时，Podman 环境会
自动先被部署。
