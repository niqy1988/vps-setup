# ADR-0004：Xray 使用 host 网络模式

- 状态：已接受（2026-06-09 落地，2026-08-31 重建）
- 范围：`xray` 组全部主机

## 背景

Xray 需支持 UDP/QUIC。rootless Podman 经 slirp4netns 的 UDP 端口映射不可靠，
Xray 使用 host 网络模式可完全规避该限制。

## 决策

Xray 以 host 网络模式（Quadlet `Network=host`）运行，监听 `127.0.0.1`
（入站端口由 `xray_*_port` 变量配置，示例见 `sample_inventory/`）。Traefik 在
`podman_network` 中经回环接口把流量转发到 Xray 后端（地址 `127.0.0.1`）。

## 影响

- Xray 不能与其他服务共享端口（宿主机端口冲突）。
- Xray 可直接访问宿主网络接口。
- Traefik ↔ Xray 流量经回环，多一跳（可忽略）。
- 未来 QUIC 支持无需额外 workaround。
