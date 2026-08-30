# ADR-0001：基础环境迁移至 Debian 13

- 状态：已接受（2026-08-21 落地）
- 范围：全部目标机（`bootstrap.yaml` / `all.yaml` 覆盖的所有主机）

## 背景

项目此前按 AlmaLinux（RHEL 系）编写：`dnf` 包管理、`firewalld` 防火墙、
SELinux（生产机 enforcing、开发机 permissive）。这套依赖链路——SELinux
自定义策略模块（`udica` / CIL）、共享数据目录的 `container_file_t` 标签、
firewalld 服务注册——与 rootless Podman 的容器权限模型叠加后引入不少坑位
（SELinux enforcing 下容器访问 `/app`、`/data` 被拒，且须配合持久
fcontext 规则才可跨重启存活）。

## 决策

目标机基础环境从 AlmaLinux 迁移至 **Debian 13（trixie）**：

- **包管理**：安装用 `ansible.builtin.package`（自动选 apt 后端）；批量升级
  用 `ansible.builtin.apt` 的 `upgrade: dist`（等价 `apt full-upgrade`）。
  中文 locale 改用 `locales-all`。
- **防火墙**：`firewalld` → `community.general.ufw`。默认拒绝入站、放行
  出站；SSH 用 ufw 的 `OpenSSH` profile（Debian 只有 `[OpenSSH]`，无
  Ubuntu 才有的 `[ssh]` 别名）。
- **SELinux 全部移除**：`podman` / `traefik` / `xray` / `filebrowser` /
  `rclone` 中的 `setype`、`sefcontext`、CIL 策略模块、
  `security_opt: label=type:...`、容器卷 `:Z` 选项一律删除。
- **`firewall_service` 角色删除**，新增 `roles/ufw_app/`：在
  `/etc/ufw/applications.d/ufw-custom` 生成应用规则后经
  `community.general.ufw` 放行（规则即时生效，无需重载）。
- **Podman Python 绑定**：`pip` 装 podman 在 Debian 13 撞 PEP 668
  （externally-managed-environment），改装 `python3-podman`（Debian 与
  RHEL9 均有同名包，跨发行版通用）。
- **SSH**：Debian 服务名为 `ssh`（无 `sshd.service`，`sshd.service` 仅是
  `ssh.service` 的 `[Install] Alias=`），自启由 `ssh.socket`（socket
  activation）负责；`/etc/ssh/sshd_config.d/` 只保留 `00-default.conf`，
  清掉云镜像的 `50-cloud-init.conf`（避免按词序覆盖安全设置）。

## 影响

- 移除约 300 行 SELinux / firewalld 相关代码与模板（CIL 模块、fcontext
  规则、`label` 安全选项、`flush_handlers` 等），各容器角色更简单。
- `docs/adr/0001~0003`（AlmaLinux 时代的 Quadlet 迁移 / Traefik ACME /
  Xray host 网络决策）已随本次迁移删除（决策要点保留在 `docs/CONTEXT.md`
  的「Architectural Decisions Summary」表）。
- 全部角色 / playbook 通过 `ansible-lint`（production profile，0 failure /
  0 warning）。
- 后续新角色（如 `filebrowser` 一类容器角色）不再需要任何 SELinux 相关
  标签或安全选项。
