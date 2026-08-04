# Role 文档规范与维护记录

> 本文档沉淀 2026-08-04 的维护任务：为 `roles/` 下全部 9 个 role 补齐中文文档、
> 建立文档脱敏与 `sample_inventory` 约定、统一提权方式、清理死变量，并记录审计结果。

## 一、Role 文档规范

`roles/` 下 9 个 role 均有 `README.md`，全部为**中文**，统一覆盖：

1. **功能概述** —— role 做什么、部署了什么
2. **角色参数** —— 来自 `meta/argument_specs.yaml` 的表格（变量 / 类型 / 必填 / 默认值 / 说明）
3. **依赖项** —— 其他 role（`meta/main.yaml` dependencies）+ Ansible 变量 / facts / 前置条件
4. **参数与 defaults 对照** —— argument_specs 中 optional 变量是否在 `defaults/main.yaml` 定义
5. **使用范例** —— playbook 调用示例；被依赖的 role（如 `user`）同时说明「直接调用 + 被依赖」两种用法

role 列表：

| Role | 定位 | 被依赖方 |
| --- | --- | --- |
| `user` | 底层基础角色（建用户） | `ansible_access` / `interactive_access` / `podman` / `rclone` |
| `ansible_access` | Ansible 远程 sudoer 账号 + facts 目录 | — |
| `interactive_access` | 交互式登录账号 + 交互工具 | — |
| `podman` | rootless Podman 环境 | `traefik` / `xray` |
| `rclone` | rootless rclone 挂载 | — |
| `traefik` | 反向代理 + ACME | `xray` |
| `wgcf` | Cloudflare WARP 设备注册（Xray wireguard 出口） | `xray` |
| `xray` | Xray 代理（VLESS + WS/XHTTP） | — |
| `firewall_service` | 向 firewalld 注册端口服务 | — |

## 二、文档脱敏规则（重要约定）

**在 role README / 通用文档中：**

- ❌ 不写 inventory 里的实际配置值：真实用户名、UID/GID、端口、路径、
  rclone 远端名、域名、邮箱、token、SSH 公钥等——一律用中性占位代替。
- ❌ 不引用真实 inventory 文件路径（`inventory/group_vars/...` 等）作为
  "本项目在哪覆盖"。
- ✅ 需要范例时统一指向 `sample_inventory/` 目录（见下）。
- ✅ 示例一律用中性占位（`example.com`、`<cf_dns_api_token>`、`<ssh_public_key>`、
  `mydrive`、`podman_user`、`/xray/proxy` 等）。

检查命令（具体敏感词清单见本地记忆 `documentation.md`——为避免本文档自身暴露，
不在此列出具体值；此处只放不含敏感值的结构性检查）：

```bash
# 真实 inventory 路径引用残留（应只出现 sample_inventory/...）
grep -rnE 'inventory/' roles/*/README.md docs/ | grep -v 'sample_inventory' || echo "无残留"
```

## 三、sample_inventory 约定

`sample_inventory/`（项目根下）是文档唯一引用的范例来源，结构：

```
sample_inventory/
├── hosts                       # 示例组：dev / prod / others / xray
├── group_vars/
│   ├── all/
│   │   ├── credentials.yaml    # ansible_access + interactive_access
│   │   ├── podman.yaml         # podman（traefik/xray/rclone 复用）
│   │   ├── rclone.yaml         # rclone（含 rclone_conf_src_dir 说明）
│   │   └── www.yaml            # traefik + xray（domains/token/users）
│   └── xray/
│       ├── credentials.yaml    # xray_clients
│       ├── wgcf.yaml           # wgcf（全必填，<xxx> 占位）
│       └── xray.yaml           # xray 路径/端口/URL
├── rclone/conf.d/sample.conf   # rclone 远端示例（脱敏）
└── host_vars/                  # 与 hosts 主机名一一对应
```

取值规则：

- **尽量与 role 的 `argument_specs` / `defaults` 默认值一致**（作为"默认配置参考"）。
- 无默认值或敏感的值（secret/password/token/ssh 公钥）统一用 `<xxx>` 占位
  （如 `<cf_dns_api_token>`、`<ssh_public_key>`、`<password>`）。
- rclone 远端示例名用 `<remote>`；`"off"` 记得加引号（YAML 1.1 布尔坑）。

## 四、提权约定（become）

- **提权在 role 内部 task 层级完成**：需要 root 的任务逐个写 `become: true`，
  让 role **自包含**，调用 play 无需 play 级 `become: true`。
- role 无法在 `meta` 声明权限需求；若依赖 play 级 become，role 换 play 调用即失败。
- 不需要 root 的任务不要加（最小权限）。
- 仅当"整个 play 所有任务统一需 root"（如 bootstrap 的 inline tasks）才用 play 级 become。
- 例外：`wgcf` 写 `/etc/ansible/facts.d/wgcf.fact` 时**不加** become——该目录
  属主是 `ansible_username`（连接用户），以 ansible 账户写入即可。
- 落地：commit `00a3233`（`ansible_access`/`interactive_access` 补 task 级 become，
  `bootstrap.yaml` 去掉对应 play 级 become）。

## 五、参数审计结果（optional 变量 vs defaults）

逐一核对各 role `argument_specs` 的 optional 变量是否在 `defaults/main.yaml` 定义：

| Role | 未在 defaults 定义的 optional 变量 | 说明 |
| --- | --- | --- |
| `user` | `password`、`ssh_public_key` | 有意：缺省 = 锁定账号 / 无 SSH 登录 |
| `interactive_access` | `interactive_ssh_public_key` | 有意：在 inventory group_vars 设置 |
| `ansible_access` | `ansible_ssh_public_key` | 有意：在 inventory group_vars 设置（无 argument_specs） |
| 其余 6 个 role | 无 | 全部 optional 变量均已定义 ✅ |

已清理的死变量：

- `traefik` 的 `certs_dir`（defaults/spec 有、tasks/templates 未引用）—— 已删除
  （commit `4480521`）。
- inventory 中同源死变量 `certs_path` —— 已删除（该文件 gitignore，仅本机生效）。
- 备注：`xray_clients` spec 文档默认 `[]`，但 `defaults/main.yaml` 有示例条目
  （不一致但由 inventory 覆盖，无功能影响，暂保留）。

## 六、本次维护提交记录（2026-08-04，分支 new_arch）

| Commit | 内容 |
| --- | --- |
| `00a3233` | refactor: 提权下放到 role 内部 task 层级，不依赖 play 级 become |
| `a3cce48` | docs: 补齐 9 个 role 中文 README + 完善 sample_inventory 示例 |
| `4480521` | chore(traefik): 移除未使用的 certs_dir 死变量及相关文档 |
