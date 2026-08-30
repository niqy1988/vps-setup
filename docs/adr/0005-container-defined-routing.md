# ADR-0005：容器定义路由（container-defined routing）

- 状态：已接受（2026-08-31 重建）
- 范围：全部经 Traefik 暴露的服务（`traefik` / `xray` / `filebrowser` 等）

## 背景

Traefik 可通过 Docker / Podman provider 读取容器 label 自动注册后端。有两种
做法：用全局动态配置文件（`traefik_dynamic.yml`）集中定义所有路由；或在每个
容器的 Quadlet `.container` 文件中内联 `traefik.http.*` labels。

## 决策

采用**容器定义路由**：每个容器的 `.container` 定义文件直接包含
`traefik.http.routers.*` 与 `traefik.http.services.*` labels，Traefik 读取后
自动注册路由。不生成 `traefik_dynamic.yml`。

## 影响

- 新容器只需自带 labels 即可接入，无需改全局路由配置。
- 路由与容器定义共处一地（高内聚）。
- 未匹配路径由 Traefik 默认返回 404（无 Nginx 兜底）。
