# ADR-0003：Traefik ACME 管理证书

- 状态：已接受（2026-06-09 落地，2026-08-31 重建）
- 范围：全部暴露 HTTPS 的主机（`traefik` 角色）

## 背景

此前证书由 `acme` 角色（`acme.sh`）获取并放到证书目录，多一个独立工具要维护，
且其他服务需要自行读取证书文件。

## 决策

用 Traefik 内置 ACME 客户端（Cloudflare DNS challenge）取代 `acme.sh`。证书存
为 `acme.json`（Traefik 配置目录内，经绑定挂载持久化）。Traefik 终结 TLS 并
转发 HTTP，后端路由由容器 label 自动发现（见 ADR-0005）。

## 影响

- 少维护一个外部工具；证书续期由 Traefik 自动处理。
- 其他服务无需再读取证书文件——Traefik 终结 TLS 后转发 HTTP。
- `acme/` 角色已删除（2026-08-04）；Cloudflare token 经环境变量注入容器
  （不引入 vault）。
