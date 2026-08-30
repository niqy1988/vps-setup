# 运维知识（ops）

本文件收录本项目部署 / 运维中的经验与操作细节。决策记录见 `docs/adr/`，历史档案
见 `docs/history.md`，架构词表见 `docs/CONTEXT.md`。

## Debian 13 迁移操作细节（2026-08-21）

目标机从 AlmaLinux 迁移至 Debian 13（trixie），决策见
[ADR-0001](adr/0001-debian13-migration.md)。以下是非决策的操作事实：

- **包管理**：安装用 `ansible.builtin.package`（自动选 apt 后端）；批量升级用
  `ansible.builtin.apt` 的 `upgrade: dist`（= `apt full-upgrade`）。全新 Debian
  首装前需 `update_cache: true`。中文 locale 用 `locales-all`。
- **防火墙**：`community.general.ufw`。默认拒绝入站、放行出站；SSH 用 ufw
  profile 名 `OpenSSH`（Debian 只有 `[OpenSSH]`，无 `[ssh]`）。
  `firewall_service` 角色已删除，由 `roles/ufw_app/` 取代。
- **podman 绑定**：`pip` 装 podman 撞 PEP 668，改装 `python3-podman`
  （Debian 与 RHEL9 均有同名包）。
- **SSH**：Debian 服务名是 `ssh`（无 `sshd.service`，`sshd.service` 仅是
  `ssh.service` 的 `[Install] Alias=`），自启由 `ssh.socket`（socket activation）
  负责；drop-in 白名单只保留 `00-default.conf`（清掉云镜像的 `50-cloud-init.conf`，
  避免覆盖安全设置）。
- **SELinux 全部移除**：各容器角色的 `setype` / `sefcontext` / CIL 模块 /
  `security_opt: label` / 卷 `:Z` 选项全部删除；`community.general.sefcontext`
  在无 SELinux 系统会失败（semanage 不存在），必须删除。

## 运行经验（2026-08-05，filebrowser 部署）

- **`containers.podman` 对 `podman_network state: quadlet` 的支持有版本门槛**：
  1.11.0 不支持（state 仅 `present/absent`），需升级到支持 quadlet 的版本
  （1.20.2 实测可用）。`podman_* state: quadlet` 的合法性不能只靠 lint——缺
  `containers` 集合时模块参数校验会被跳过。
- **`lookup('file')` 相对路径以 playbook 所在目录为基准**（非控制机 cwd）：
  读取 `inventory/...` 等控制端文件时，相对路径默认值在 `playbooks/` 子目录下会
  失效（解析成 `playbooks/inventory/...`）。改用 `{{ inventory_dir }}/...`
  绝对基准。
- **`state: touch` 非幂等**：`file` 模块 touch 默认
  `modification_time/access_time = now`，每次更新 mtime 恒报 changed；设
  `modification_time: preserve` / `access_time: preserve` 即幂等，且仍会校验 /
  修正 owner/group/mode。
- **argument_specs 嵌套校验会拦 CLI 风格连字符键名**：host vars 里 rclone mount
  用 `vfs-cache-size` 被嵌套 options 校验拒绝；应用下划线变量名 `vfs_cache_size`。
- **gtsteffaniak fork 的 WebDAV 端点是 `/dav/<source>/`**（需源名，如
  `/dav/Data/`），裸 `/dav` 返回 404 属正常；WebDAV 用 filebrowser 自带
  Basic Auth（用户名 + JWT token）。
- **幂等性**：filebrowser 自身已全幂等（db touch 用 preserve）；依赖 role 仍有
  少量非幂等（如 traefik auth 中间件因 bcrypt 随机盐每次 changed），属既有问题
  待单独优化。

## 历史经验（适用于 2026-08-21 之前的 AlmaLinux 目标机）

> 以下 SELinux 相关条目仅适用于迁移前的 AlmaLinux（SELinux）环境；自 2026-08-21
> 起项目使用 Debian 13，不再使用 SELinux。保留供历史参考。

- **SELinux**：容器（`container_t`）访问 `user_home_t` 类型的文件会产生 AVC
  （permissive 记录、enforcing 拒绝）；容器读写的文件应标 `container_file_t`。
- **SELinux enforcing 下容器访问 `/data` 失败**：`/data` 原为 `default_t`，
  enforcing 下容器 `container_t` 访问被拒（`ls: Permission denied`）。修复：对
  `/app`、`/data` 用 `file` 模块 `setype: container_file_t` + 持久 fcontext 规则
  （`community.general.sefcontext`）。
