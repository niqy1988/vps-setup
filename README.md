# vps-setup

基于 Ansible 的 VPS 自动化配置仓库：用一套角色（role）+ Playbook + 示例
inventory，把裸机 VPS 从零配置为可用的代理 / 存储服务器。

当前核心架构为 **rootless Podman（Quadlet）+ Traefik + Xray** 反代与代理栈，
并支持 rclone 云盘挂载、Cloudflare WARP 出口等扩展。

> 架构上下文、术语表、主机组与设计决策见 [docs/CONTEXT.md](docs/CONTEXT.md) 与
> [docs/adr/](docs/adr/)。

## 特性

- **rootless Podman + Quadlet**：容器以非 root 用户运行，用声明式
  `.container` / `.network` 定义管理生命周期（ADR-0001）。
- **Traefik 反向代理 + ACME**：Cloudflare DNS challenge 签发证书，通过容器
  label 自动发现路由（container-defined routing），无 Nginx 兜底（ADR-0002）。
- **Xray 代理**：VLESS + WebSocket / XHTTP，host 网络模式保留 UDP/QUIC
  兼容性（ADR-0003），经 Traefik 暴露 HTTPS 入口。
- **wgcf 出口**：注册 Cloudflare WARP 设备，为 Xray 提供 WireGuard 出口。
- **rclone 挂载**：rootless systemd user service 按需挂载云盘（VFS 缓存）。
- **账号与权限**：`user` / `ansible_access` / `interactive_access` 统一管理
  系统用户、sudo 与 SSH 公钥。
- **提权约定**：提权下沉到 role 内部 task 层级，role 自包含，调用 play 无需
  play 级 `become: true`。

## 目录结构

```text
.
├── ansible.cfg            # 连接用户 / inventory / roles_path 配置
├── requirements.yaml      # 依赖的 Ansible collection
├── playbooks/             # 顶层 Playbook（all / bootstrap / xray / ...）
├── roles/                 # 正式角色（10 个，均带中文 README）
├── legacy_roles/          # 已废弃的旧角色（_plex / _qbittorrent）
├── inventory/             # 私有 inventory（git 忽略），镜像 sample_inventory 结构
├── sample_inventory/      # 文档唯一引用的范例 inventory（已脱敏）
├── docs/                  # 文档（架构上下文 / 规范 / lint 记录 / ADR）
└── tests/                 # 遗留测试 playbook（与当前架构脱节，待清理）
```

## 前置要求

- 控制机：macOS / Linux，能通过 SSH 访问目标 VPS。
- 目标机：AlmaLinux 系（本项目按 dnf / firewalld / SELinux 编写）。
- SSH 凭据：私钥全链路不指定，交给 ssh-agent + OpenSSH 自动发现；公钥由
  `user` / `ansible_access` 等角色以文本形式部署到目标机。

## 快速开始

```shell
# 1. 安装 uv 与 ansible（含 ansible-core / ansible-lint）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --python 3.14 --with "bcrypt<5" --with libpass --with-executables-from ansible-core,ansible-lint ansible

# 2. 安装依赖的 collection
ansible-galaxy install -r requirements.yaml

# 3. 准备 inventory：以 sample_inventory/ 为模板，复制/改造成自己的私有
#    inventory（占位符全部替换为真实值；真实 inventory 目录被 git 忽略）

# 4. 初始化基础环境（SSH 密钥登录、firewalld、BBR、/app /data 目录等）
ansible-playbook playbooks/bootstrap.yaml

# 5. 部署全部服务（import bootstrap + xray）
ansible-playbook playbooks/all.yaml
```

> 依赖 GitHub 网络受限时，可配置本地代理后重试；控制机 SSH 凭据走
> ssh-agent + OpenSSH 自动发现，Ansible 侧不指定私钥路径。

## 主机组

| 组 | 用途 |
| --- | --- |
| `prod` | 生产机：镜像指定版本、SELinux enforcing、默认不允许交互式登录 |
| `dev` | 开发机：镜像 latest、SELinux permissive、允许交互式登录 |
| `interactive` | 允许交互式登录的生产机 |
| `xray` | 部署 Xray 代理栈的主机（podman + traefik + wgcf + xray 全套） |

主机可同时属于多个组。组的具体构成与主机级变量示例见 `sample_inventory/`。

## Playbook

| Playbook | 说明 |
| --- | --- |
| `all.yaml` | 总入口：import `bootstrap.yaml` + `xray.yaml` |
| `bootstrap.yaml` | 初始化基础环境：ansible 管理账号、时区、官方镜像源（mirrorlist）、EPEL / CRB、关键软件包、firewalld、BBR、目录等 |
| `xray.yaml` | 更新 `xray` 组软件包 + 部署 `xray` 角色 |
| `file_server.yaml` | 部署 `filebrowser` 角色（默认 `file` 组） |
| `update_packages.yaml` | 升级全部主机软件包 |
| `debug_print.yaml` | 调试：打印控制机 / 远端变量与主机名 |
| `sandbox.yaml` | 本地探索 / 临时任务（不用于生产） |

## 角色一览

| Role | 定位 | 说明 |
| --- | --- | --- |
| [`user`](roles/user/README.md) | 底层基础角色 | 建用户 + subuid/subgid + sudo + linger，被多个角色依赖 |
| [`ansible_access`](roles/ansible_access/README.md) | Ansible 远程管理 | sudoer 账号 + facts 目录 |
| [`interactive_access`](roles/interactive_access/README.md) | 交互式登录 | 交互账号 + 交互工具 |
| [`podman`](roles/podman/README.md) | rootless Podman 环境 | 被 `traefik` / `xray` 依赖 |
| [`rclone`](roles/rclone/README.md) | rootless rclone 挂载 | 按 remote 挂载云盘 |
| [`traefik`](roles/traefik/README.md) | 反向代理 + ACME | 容器 label 自动发现路由 |
| [`wgcf`](roles/wgcf/README.md) | Cloudflare WARP 注册 | 产出 Xray 的 WireGuard 出口 |
| [`xray`](roles/xray/README.md) | Xray 代理 | VLESS + WS / XHTTP |
| [`firewall_service`](roles/firewall_service/README.md) | firewalld 端口服务 | 向 firewalld 注册服务 |
| [`filebrowser`](roles/filebrowser/README.md) | Web 文件管理 + WebDAV | Quadlet 容器，经 Traefik 路由 |

各角色参数（`argument_specs`）、依赖、范例见各自 README；示例变量统一见
`sample_inventory/`。

## 文档

- [docs/CONTEXT.md](docs/CONTEXT.md) —— 架构上下文、术语、主机组、决策记录。
- [docs/adr/](docs/adr/) —— 架构决策记录（Quadlet 迁移 / Traefik ACME /
  Xray host 网络）。
- [docs/role-doc-conventions.md](docs/role-doc-conventions.md) —— Role 文档
  规范、脱敏规则、`sample_inventory` 约定、提权约定、参数审计记录。
- [docs/ansible-lint.md](docs/ansible-lint.md) —— ansible-lint 整理记录
  （各 role / playbook 达标过程、noqa 清单、工具用法）。

## 维护约定

- **文档脱敏**：role / 通用文档不得出现 inventory 中的实际配置值（真实用户名、
  UID/GID、端口、路径、rclone 远端名、域名、邮箱、token、SSH 公钥等），一律用
  中性占位（`example.com`、`<cf_dns_api_token>`、`<ssh_public_key>` 等）；
  需要范例时统一指向 `sample_inventory/`。详见 `docs/role-doc-conventions.md`。
- **提权**：需要 root 的任务在 role 内部逐个 `become: true`，让 role 自包含。
- **Lint**：`roles/` 与 `playbooks/` 均为 0 failure / 0 warning（production
  profile）；改动后建议跑 `ansible-lint` 验证。
- **架构变更**：先更新 `docs/CONTEXT.md` / `docs/adr/`，再动代码。

## License

GPL-3.0，见 [LICENSE](LICENSE)。