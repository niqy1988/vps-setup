# ADR-0004：Xray 加入 podman_network 容器网络

- 状态：已接受（2026-08-31 修正：原"host 网络"表述与代码不符，Xray 实际加入
  `podman_network`）
- 范围：`xray` 组全部主机

## 背景

早期设计曾考虑 Xray 用 host 网络以规避 rootless Podman 的 UDP 端口映射限制。
实际落地中 Xray 容器与 Traefik 同处 `podman_network` 容器网络，不采用
host 网络。

## 决策

Xray 容器挂到 `podman_network`（Quadlet `Network={{ podman_network }}.network`），
与 Traefik 同网。入站端口（`xray_*_port`）为容器内监听端口；Traefik 经
podman provider 读取 Xray 容器 label
（`traefik.http.services.*.loadbalancer.server.port`），在容器网络内经对应
server port 直连 Xray。

## 影响

- Xray 与 Traefik 在同一容器网络内直连，无需 host 回环。
- 不再受"host 网络与宿主机端口冲突"限制。
- 网络拓扑与 Traefik / Xray 的 label 路由一致（见 ADR-0005）。
