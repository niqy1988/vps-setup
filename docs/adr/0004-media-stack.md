# ADR-004: Media stack — BT downloads on local disk, Arr imports into the cloud mount

- **Status:** Accepted
- **Date:** 2026-08-05
- **Scope:** `download` / `media` 组主机（媒体服务器）。
- **Context:** 需要 qBittorrent 下载 + Sonarr/Radarr 搜寻与管理媒体库 + Plex
  读取。媒体库最终落在云端（rclone 挂载）的 `Media` 目录。rclone VFS 缓存
  对 BT 下载不友好（官方文档确认）：打开中的文件不可被驱逐（缓存会被下载中/
  做种中的 torrent 钉死）；写入仅在文件 close 且闲置超过 `--vfs-write-back`
  后才上传（`.parts` 永不传、崩溃丢缓存）；云对象存储不支持部分写（BT 随机写
  = 整块重传的上传放大）。若让 qBittorrent 直写挂载，这些风险全部命中。
- **Decision:** BT 下载落地**本地真实盘**（`/data/Downloads`，与 rclone 挂载
  解耦）；Sonarr/Radarr 完成后以「顺序整文件写 → close → 后台自动上传」
  （VFS full cache 的甜点场景）导入媒体库挂载；Plex 读挂载。
  - 新增 4 个角色：`qbittorrent`、`sonarr`、`radarr`、`plex`，全部 rootless
    Quadlet + Traefik 容器标签路由 + Cloudflare DNS CNAME。
  - qBittorrent WebUI 走 Traefik（`bt.<domain>`，挂 `traefik-auth@file`），
    BT 监听端口发布并开放 firewalld；WebUI 端口不对外发布。
  - 媒体库根目录 `/data/Media` 符号链接到 `/mnt/rclone/<mount>/Media`；
    若 `/data/Media` 已存在为真实目录（旧配置遗留），角色显式失败提示迁移，
    避免静默走本地路径。
  - `rclone` 角色增加可选 VFS 读/目录缓存参数（`vfs_read_ahead`、
    `vfs_read_chunk_size`、`vfs_read_chunk_streams`、`dir_cache_time`），
    供 Plex 流媒体平滑与 Arr 扫描调优。
  - 备选方案：**Option B**（本地硬链接媒体库 + 独立 rclone 定时上云）适合
    seeding 党，但需额外 mover 组件且有云/本地一致性与可见延迟成本；
    **Option C**（qBittorrent 直写挂载）风险过高不采用。当前采用 Option A。
- **Consequences:**
  - BT 与 VFS 解耦：崩溃/续传安全（`.parts` 在本地盘），无缓存钉死/上传放大。
  - Arr 导入即写 VFS 缓存、上传异步后台，新片对 Plex 可见及时。
  - 本地盘需为下载/做种留余量：建议 VFS 缓存上限设为盘容量 50–60%，或用
    `vfs_cache_min_free_space` 保留下载余量（待确认实际盘容量后调参）。
  - Plex 在 FUSE 挂载上 inotify 不生效 → 需开启定时扫描（支持 change
    notification 的远端可及时刷新目录列表，但 Plex 侧仍需定时触发）。
  - rootless Podman 发布 UDP 端口的可靠性取决于网络后端（slirp4netns/pasta）；
    TCP 一般可靠。若实测 uTP/DHT 不可用，可评估回退 host 网络模式
    （WebUI 绑 `127.0.0.1`，沿用 ADR-003 的思路）。
  - qBittorrent 配置（含 WebUI 密码 PBKDF2 哈希）与分类在首次部署时播种，
    之后由 qBittorrent 自行管理，保证幂等。
  - `legacy_roles/_plex`、`_qbittorrent` 已被新角色取代（遗留待清理，见
    `docs/CONTEXT.md` TODO）。
