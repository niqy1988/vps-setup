# ansible-lint 整理记录（roles + playbooks）

> 本文记录 `roles/` 下 9 个 role 与 `playbooks/` 下 6 个 playbook 的 lint 达标过程：每个文件改了什么、哪些违规是**有意忽略/豁免**的及原因、以及过程中用户提出的疑问与最终结论。
> 配套记忆：`/memories/repo/lint.md`（精简版 + 实时状态）。

## 环境与当前状态

- **ansible-lint 6.22.2**（uv 安装，运行时有 `PATH altered` 警告但可用）。
- 项目**无 `.ansible-lint` 配置文件**，也**不用 `.ansible-lint-ignore`**（2026-08-04 已删除，见「疑问 1」）。
- 分支 `new_arch`，工作区干净。
- **当前验证命令与结果**：
  - `ansible-lint roles/` → `0 failure(s), 0 warning(s)` on 61 files，production profile。
  - `ansible-lint playbooks/` → `0 failure(s), 0 warning(s)`（production profile，19 files），见「playbooks 的 lint 整理记录」。
  - 单 role：`ansible-lint roles/<role>` 同样 0/0。
  - 全项目 `ansible-lint`（无参数）→ 报 **3 个 fatal** `syntax-check[specific]`，全在 `tests/`（`file_server.yaml:23` filebrowser / `media_server.yaml:21` plex / `seedbox.yaml:21` qbittorrent）——**有意保留**，见「疑问 8」。

## playbooks 的 lint 整理记录（2026-08-04）

> 覆盖 `playbooks/` 下 6 个文件（`all.yaml` / `bootstrap.yaml` / `debug_print.yaml` / `sandbox.yaml` / `update_packages.yaml` / `xray.yaml`）。`tests/` 不参与——指定 `playbooks/` 路径即避开。

### 当前状态
- `ansible-lint playbooks/` → **0 failure / 0 warning**（production profile，19 files）。
- 有意豁免 3 处：`state: latest` 行尾内联 `# noqa: package-latest`（纯升级语义，见「noqa 清单」）。

### 达标过程（78 → 0）
- **78 → 11**（修无争议项）：FQCN 补全（`package`/`file`/`copy`/`systemd_service`/`reboot`/`find`/`replace`/`cron`/`debug`→`ansible.builtin.*`，`acl`→`ansible.posix.acl`，`sysctl`→`ansible.posix.sysctl`）；`name[play]`/`name[missing]`/`name[casing]`；`risky-file-permissions` 目录 `file`/`copy` 补 `mode`；handler `shell`→`command` + `changed_when: false`。
- **11 → 6**（用户）：各 `Install X` 任务由 `state: latest` 改 `state: present`（Chinese locale / Python / ACL / SELinux / firewalld / PowerTools / EPEL）。
- **6 → 4**：3 处升级语义 `name: "*"` 的 `package-latest` 加行尾 `# noqa: package-latest`。
- **4 → 0**：`bootstrap.yaml` timezone 的 reboot 由任务改 handler（`notify` + handlers 块，去掉 `register: tz_result`），消除 `no-handler`。

### 各文件改动
- **all.yaml**：两个 `import_playbook` 补 `name`（`name[play]`）。
- **update_packages.yaml**：play 名 `dnf upgrade all` → `Upgrade all packages with dnf`（`name[casing]`）；`package` → `ansible.builtin.package`；升级语义保留 latest + noqa。
- **xray.yaml**：`package` → `ansible.builtin.package`；升级语义保留 latest + noqa。
- **debug_print.yaml**：`debug` → `ansible.builtin.debug`；两个 `debug` 任务补 `name`（`name[missing]`）。
- **bootstrap.yaml**：FQCN 补全；两个 `Refresh dnf cache` handler `shell: dnf makecache` → `ansible.builtin.command` + `changed_when: false`；`Create app folder` 补 `mode: "0755"`；SELinux 任务名 `enable`→`Enable`（`name[casing]`）；timezone reboot 任务→handler；各 `Install X` 改 `state: present`；`Update existing packages` 保留 latest + noqa。
- **sandbox.yaml**：FQCN 补全（`package`/`file`/`copy`/`systemd_service`→`ansible.builtin.*`，`acl`→`ansible.posix.acl`）；任务名首字母大写；目录/`copy` 补 `mode`。**第一段 `Set up rclone` play 已由用户删除**（rclone role 开发完成不再需要）。

### noqa 清单（有意豁免）
| 文件 | 任务 | noqa | 原因 |
| --- | --- | --- | --- |
| `bootstrap.yaml` | Update existing packages | `# noqa: package-latest` | 显式升级任务（`name: "*"`） |
| `update_packages.yaml` | Update packages | `# noqa: package-latest` | 整本 playbook 即 `dnf upgrade all` |
| `xray.yaml` | Update packages | `# noqa: package-latest` | 同上，显式升级 |

### playbooks 相关疑问与结论
- **为什么不要 `state: latest`，哪些可改 `present`？** `latest` 破坏幂等（每次可能 changed）、结果不可控、升级有副作用。标准：**"确保已装"→`present`；"升级到最新"→`latest`（且放独立 playbook）**。bootstrap 里 7 处 `Install X` 改 present；3 处 `name: "*"` 的升级任务保留 latest。
- **reboot 改 handler 后何时触发？** handler 在**当前 play 结束**时 flush（非 playbook 结束）。`Update timezone` play 只有 2 个任务，行为与原来任务形式等价；timezone 未变则 reboot 不触发（handler 仅被 notify 且 changed 才运行），保留原语义。
- **role 内 3 处 `flush_handlers` 是否必要？** 均**必要**，保留：`firewall_service`（`firewalld` 模块需 service 已 reload 才认）；`podman`（被 traefik/xray 经 `meta` 依赖、同 play 先执行，网络须在容器启动前建好）；`traefik`（容器 `security_opt: label=type:traefik_container.process` 须在 SELinux policy 加载后才启动）。通用判断标准：**handler 的效果是否被同一 play 内后续任务依赖**。

## 各 role 的 lint 过程（按 git 提交）

### user（`f88479c` + `fc1ca4f`）— 底层基础 role
- **FQCN 补全**：`group`/`set_fact`/`user`/`lineinfile`/`file`/`command`/`copy` → `ansible.builtin.*`。
- **name[casing]**：任务名首字母大写。
- **key-order[task]**：`block` 的 `when` 移到 `name` 之后、`block` 之前。
- **command-instead-of-shell**：`loginctl enable/disable-linger` 的 `shell` → `command`（带 `creates`/`removes`）。
- 清理尾随空格、文件末尾补换行。
- **var-naming[no-role-prefix]**：`uid`/`sudoer`/`linger` 行尾内联 `# noqa` 豁免（底层 role，公开参数保持通用名）。`user_groups` 以 `user_` 开头符合前缀，无需 noqa。

### ansible_access / firewall_service / interactive_access（`fc1ca4f`）
- **FQCN 补全**：`file`/`meta`/`template`/`systemd_service`/`package` → `ansible.builtin.*`。
- **risky-file-permissions**：目录 `file` 补 `mode: "0755"`、`template` 补 `mode: "0644"`。
- 清理尾随空格、文件末尾补换行。
- **var-naming[no-role-prefix]**（行尾内联 noqa）：
  - `ansible_access`: `ansible_username`、`ansible_uid`
  - `firewall_service`: `tcp_ports`、`udp_ports`
  - `interactive_access`: `interactive_password`、`interactive_uid`、`interactive_user_groups`、`interactive_sudoer`

### podman（`ac5f69f`）
- **FQCN 补全**：`package`/`pip`/`file`/`meta`/`systemd_service`/`include_tasks` → `ansible.builtin.*`；`sysctl` → `ansible.posix.sysctl`。
- **name[casing]**：首字母大写，并修正 typo `unpriviledged` → `unprivileged`。
- 清理尾随空格、`defaults/main.yaml` 末尾补换行。
- **`state: quadlet` 加行尾 `# noqa: args[module]`**：`containers.podman.podman_network` 的 `state` 官方 `choices=present/absent/quadlet`，`quadlet` 合法，lint 的 `args[module]` 是**误报**（见「疑问 4」）。

### traefik（`5bf381d`）
- **FQCN 补全**：`systemd_service`/`file`/`copy`/`meta`/`template`/`command`（handlers 同）→ `ansible.builtin.*`。
- **risky-file-permissions**：2 个目录 `file` 补 `mode: "0755"`、logrotate `template` 补 `mode: "0644"`。
- **var-naming[no-role-prefix]**：`podman_network`、`acme_email`、`cloudflare_dns_api_token` 行尾内联 noqa（名字**保留待审查**，见「疑问 3」）。

### xray（`c76fac0`）
- **FQCN 补全**：`file`/`template`/`systemd_service`（handlers 同）→ `ansible.builtin.*`。
- **risky-file-permissions**：2 个目录 `file` 补 `mode: "0755"`、logrotate `template` 补 `mode: "0644"`。
- **var-naming[no-role-prefix]**：`domains`、`cloudflare_dns_api_token` 行尾内联 noqa（**用户决定不改名**，与 traefik 一致做法）。

### wgcf（`c76fac0`）
- **FQCN 补全**：`package`/`command`/`shell`/`set_fact`/`uri`/`copy`/`setup` → `ansible.builtin.*`。
- **name[casing]**：2 处 `set_fact` 任务名首字母大写。
- **key-order[task]**：`Register new device` 的 `block` 把 `when` 移到 `name` 之后、`block` 之前。
- **command-instead-of-shell**：`shell: "wg genkey"` → `command: wg genkey`。
- **risky-shell-pipe**：`echo ... | wg pubkey` 加 `cmd: "set -o pipefail && ..."` + `executable: /bin/bash`（判定是行首 `set.*-o pipefail` 正则，须整句开头 `set`）。
- 两个生成 key 的 `command`/`shell` 补 `changed_when: true`。
- `copy`（persist fact）补 `mode: "0644"`。
- 清 5 处尾随空格（`argument_specs.yaml:4`、`tasks/main.yaml:4/33/78/84`）。

### rclone（无专门 lint 提交，仅 `f88479c` 顺带规范化）
- `acl` 用 `ansible.posix.acl`；`lineinfile`/`template` 需显式 `mode`。
- `meta/argument_specs.yaml` 的 `choices` 里 `'off'` **必须加引号**（YAML 1.1 会把裸 `off` 解析成布尔 `False`），用户传值同样写 `"off"`（见「疑问 6」）。
- `f88479c` 顺带把 `choices: ['off','minimal','writes','full']` 的单引号规范化为双引号 `["off", "minimal", "writes", "full"]`（纯格式，无行为变化）。

## 需要忽略的违规（noqa 清单）与原因

| 文件 | noqa | 原因 |
| --- | --- | --- |
| `roles/user/defaults/main.yaml`（uid/sudoer/linger） | `var-naming[no-role-prefix]` | 底层基础 role，公开参数保持通用名（`user_groups` 以 `user_` 开头无需 noqa） |
| `roles/ansible_access/defaults/main.yaml` | `var-naming[no-role-prefix]` | 通用 SSH 用户名/uid，不属该 role 专属 |
| `roles/firewall_service/defaults/main.yaml`（tcp_ports/udp_ports） | `var-naming[no-role-prefix]` | 通用端口变量 |
| `roles/interactive_access/defaults/main.yaml` | `var-naming[no-role-prefix]` | 交互用户参数保持通用名 |
| `roles/traefik/defaults/main.yaml`（podman_network/acme_email/cloudflare_dns_api_token） | `var-naming[no-role-prefix]` | 跨 role 共用参数，保持通用名（待审查是否加 `traefik_` 前缀） |
| `roles/xray/defaults/main.yaml`（domains/cloudflare_dns_api_token） | `var-naming[no-role-prefix]` | 与 traefik 共用 token 变量，不改名 |
| `roles/podman/tasks/main.yaml`（`state: quadlet`） | `args[module]` | 官方 `choices` 含 `quadlet`，lint 误报（需本地装 `containers` 集合才能消掉，故 noqa） |

> **noqa 用行尾内联而非 `.ansible-lint-ignore`**：行尾 `# noqa:` 只豁免该行，且随文件走——无论 VS Code 扩展以何种方式调用 ansible-lint 都生效（见「疑问 1」）。

## 其他无害 warning（非 failure，无需处理）

- `Ignored exception ... No module named 'containers'`：本地缺 `containers` 集合，`podman_container`/`podman_network` 参数校验被跳过，纯 warning，不影响结果。
- `The following filters were mocked during the run: url_query,decode_wgcf_reserved`：lint 静态分析时加载不到 `roles/wgcf/filter_plugins/wgcf_filters.py` 的真实实现，用 mock 顶替让模板能继续解析——只是对这两个 filter 的模板**静态校验降级**，真实运行时 Ansible 正常加载，行为正确。

## 用户疑问记录（含最终结论）

1. **VS Code 里为什么还显示 lint error？** 扩展调用 ansible-lint 的方式（工作目录/单文件）读不到项目根 `.ansible-lint-ignore`。**结论**：弃用 ignore 文件，全部改用文件内**行尾内联 `# noqa`**，随文件生效，与调用方式无关。这是本项目统一约定。
2. **用 `.ansible-lint-ignore` 还是内联 noqa？** 最初用 ignore 文件（会显示 `# ignored` 的 warning），后因疑问 1 改内联，达到真正的 **0 warning**。最终：内联 noqa。
3. **要不要给公开参数加 role 前缀改名？** traefik 的 `podman_network`/`acme_email`/`cloudflare_dns_api_token`、xray 的 `domains`/`cloudflare_dns_api_token` 均**暂不改名**，用 noqa 豁免；traefik 提交信息标注 "names kept pending review"，待日后审查。
4. **`state: quadlet` 是不是非法值？** 查官方源码确认 `containers.podman.podman_network` 的 `choices = present/absent/quadlet`，`quadlet` **合法**。lint 报的 `args[module]` 是误报（因本地缺 `containers` 集合导致参数校验异常），用 `# noqa: args[module]` 豁免。
5. **`-t fqcn,name` 组合查询为什么跑出 yaml 规则？** 6.22.2 的 bug：组合 tag 会异常触发 yaml 规则。**结论**：按 rule id 单独用 `-t fqcn`、`-t name` 更稳。
6. **rclone 的 `off` 是不是非法值？** 用户纠正过：`--vfs-cache-max-size` / `--vfs-cache-min-free-space` 官方**默认就是 `off`**（表示不限制），传 `off` 完全合法。**教训**：改代码前先查官方文档，别凭记忆。
7. **`best: false` 为什么报错？** `dnf` 模块**没有** `best` 参数（那是 `yum` 模块的）；表达"不强制最佳候选"用 `nobest: true`。（2026-08-04 已修）
8. **全项目 lint 的 3 个 fatal（tests/ 引用旧 role）？** `tests/` 引用 `filebrowser`/`plex`/`qbittorrent`，role 已改名 `_*` 并移入 `legacy_roles/`。**用户决定放着不管**（tests 待整体废弃/重写），勿改 tests 或旧 role 名。
9. **`--fix` 能不能直接用？** `--fix=fqcn,name` 有副作用：文档明示 "YAML reformatting happens whenever '--fix' is used"，会顺带去字符串引号、给无 `---` 的 YAML 加文档头、删多余空行。**结论**：用 `--fix` 后须 `git diff` 审查非目标行，或纯手动改。

## 工具用法速查

```bash
# 列出所有规则及 tag
ansible-lint -L
ansible-lint -T

# 只查特定规则（按 rule id 最精确，别组合，见疑问 5）
ansible-lint -t fqcn
ansible-lint -t name

# 单 role 校验
ansible-lint roles/<role>

# syntax-check 的 tag 是 core,unskippable，-t 躲不掉，只能 --exclude
ansible-lint -t fqcn --exclude <path>
```

## 常用坑位

- **尾随空格**：处理时先 `cat -e` / `od -An -tx1` 确认精确空格数，别凭 `nl` 输出肉眼估（`nl` 前缀会干扰判断）。
- **YAML 1.1 布尔坑**：未加引号的 `off`/`on`/`yes`/`no` 会被解析成布尔；要字面字符串必须加引号（rclone choices、传"关闭/不限"值时尤其注意）。
- **含 `{{ }}` 的字符串值尽量加双引号**；`ansible-lint --fix` 可能把引号去掉，用完后检查加回。
