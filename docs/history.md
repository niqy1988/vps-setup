# 历史档案（history）

本文件记录已发生的历史变更、已删除的角色 / 决策与遗留问题。当前架构词表见
`docs/CONTEXT.md`，决策见 `docs/adr/`，运维知识见 `docs/ops.md`。

## 架构沿革

- **2026-06**：以单台主机起步；容器用 Quadlet（ADR-0002）、证书用 Traefik ACME
  （ADR-0003）、Xray 用 host 网络（ADR-0004）。
- **2026-08-04**：架构铺开到 `xray` 组全部主机；删除 acme / nginx 角色；文档全量
  脱敏。
- **2026-08-05**：filebrowser 角色落地（Traefik 标签路由 + rclone 挂载）。
- **2026-08-21**：目标机迁至 Debian 13（ADR-0001）；删除 firewall_service 与全部
  SELinux 代码；删除旧 ADR-0001~0003（核心决策已重建为 ADR-0002~0004）。

## 已删除的角色

- `roles/_acme/` — acme.sh 证书管理，已被 Traefik ACME 取代（ADR-0003）
- `roles/_nginx/` — nginx 反向代理，已被 Traefik + 容器标签路由取代（ADR-0005）
- `roles/firewall_service/` — firewalld 时代端口服务，已被 `roles/ufw_app/` 取代
- `legacy_roles/_filebrowser/` — 已被正式 `roles/filebrowser/` 取代
- 媒体角色（`plex` / `qbittorrent` / `sonarr` / `radarr`）在 `download_pack` 分支
  开发后未合入 main，现磁盘仅残留空目录 / 缓存；媒体栈已搁置、规划后续开发
  （见 `docs/CONTEXT.md` Roadmap）

## 被取代的历史决策（原 CONTEXT 决策表条目）

以下条目已从 CONTEXT 决策表移除（被 ADR 或现状取代，或属冗余重复）：

- Nginx 移除（原 #1 / #22，重复）→ ADR-0005（容器标签路由，无 Nginx 兜底）
- Traefik ACME 取代 acme.sh（原 #2）→ ADR-0003
- Xray host 网络（原 #3）→ ADR-0004
- Quadlet 定义用 J2 模板（原 #7 / #8）→ **已过时**：现用 `state: quadlet` 模块
  生成定义文件（ADR-0002），不手写 J2 模板
- Xray 支持 ws + xhttp 单入口（原 #13 / #21，重复）→ 现状由 `xray_*_port` 变量配置
- argument_specs 作为主文档（原 #12）→ 仍适用，属角色约定（见
  `docs/role-doc-conventions.md`）
- 防火墙在 traefik role handler 打开 80/443（原 #16）→ 现状 ufw 即时放行
- 其余（#4 / #5 / #6 / #9 / #10 / #11 / #14 / #15 / #17 / #18 / #19 / #20 / #24 /
  #25）为既有实现约定，已沉淀在各角色 README 与 ADR 中

## 遗留问题（Known leftover issues）

- `tests/` 整体与当前项目脱节，引用不存在的角色：`plex`（`media_server.yaml`）、
  `qbittorrent`（`seedbox.yaml`）、`hath`（`hath.yaml` 注释）——待整体废弃 / 重写。
- `legacy_roles/_plex`、`_qbittorrent` 依赖已删除的 `firewall_service` 角色，无法
  直接运行，仅供历史参考。
- 磁盘 `roles/{plex,qbittorrent,radarr,sonarr,hath}` 残留空目录 / `__pycache__`
  （git 未跟踪），可安全清理。
- 私有 inventory `group_vars/{dev,prod}/selinux.yaml` 含无引用的 `selinux_mode`
  残留变量（gitignored，不提交）。

## TODO

- [ ] 清理 / 重写 `tests/` 目录，删除或迁移引用已不存在 role 的测试场景
- [ ] 媒体栈（已搁置、规划中）：从 `download_pack` 分支合入或在主线上重建
- [ ] 清理磁盘残留角色目录与私有 inventory 的 `selinux_mode` 残留
