# ADR-0002：Quadlet 声明式容器定义

- 状态：已接受（2026-06-09 落地，2026-08-31 重建）
- 范围：全部容器类角色（`podman` / `traefik` / `xray` / `filebrowser`）

## 背景

Podman 服务可用命令式 `containers.podman.podman_container`（`state: present`，
直接在主机上启动容器），或用声明式 Quadlet `.container` / `.network` /
`.volume` 定义文件（由 systemd 用户会话管理生命周期）。较新的
`containers.podman` collection 支持 `state: quadlet`——Ansible 传结构化参数
（镜像、网络、健康检查、labels、卷…），由模块直接渲染定义文件到
`~/.config/containers/systemd/`，不启动任何容器。

## 决策

用 `containers.podman.podman_container`（及 `podman_network`、`podman_volume`）
的 `state: quadlet` 生成 Quadlet 定义文件。生成后触发
`systemctl --user daemon-reload` 与 `enable --now`。

## 影响

- 容器生命周期由 systemd 用户会话管理，符合 rootless 最佳实践。
- 无需手写 J2 模板——模块参数类型化、文档化，在 playbook 期校验。
- `argument_specs.yaml` 与模块字段直接对应，兼作 API 文档与默认值。
- 回滚 = `systemctl --user disable --now` + 清理生成的定义文件。
- 需要支持 `state: quadlet` 的 `containers.podman` 版本（本项目用 1.20.2；
  1.11.0 不支持）。
