# interactive_access 角色

设置一个用于交互式 shell 访问的远程账号，并安装 `screen`、`tree` 等
日常交互工具。

## 功能概述

1. 通过依赖的 [`user`](../user/README.md) 角色创建交互账号（可带密码、
   SSH 公钥、额外用户组、sudo 权限）。
2. 安装 `screen`、`tree` 工具。
3. `reset_connection` 重置 SSH 连接使变更立即生效。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `interactive_username` | str | ✅ 是 | — | 用户名 |
| `interactive_password` | str | 否 | `"!"` | 用户密码（`no_log`）；缺省为 `"!"`（锁定） |
| `interactive_ssh_public_key` | str | 否 | **无默认**（见下） | SSH 公钥文本（非文件路径） |
| `interactive_uid` | int | 否 | `100000` | 用户 UID/GID |
| `interactive_user_groups` | list\[str\] | 否 | `["users"]` | 额外用户组 |
| `interactive_sudoer` | bool | 否 | `false` | 是否授予 sudo 权限 |

> ⚠️ `interactive_ssh_public_key` **未在 `defaults/main.yaml` 定义**——
> 属有意为之，应在 inventory 中设置
> （示例见 `sample_inventory/group_vars/all/credentials.yaml`）。

## 依赖项

- **其他 role**：依赖 [`user`](../user/README.md) 角色（见
  `meta/main.yaml`）：
  ```yaml
  dependencies:
    - role: user
      username: "{{ interactive_username }}"
      password: "{{ interactive_password }}"
      ssh_public_key: "{{ interactive_ssh_public_key }}"
      user_groups: "{{ interactive_user_groups }}"
      uid: "{{ interactive_uid }}"
      sudoer: "{{ interactive_sudoer }}"
      comment: "interactive user {{ interactive_username }}"
  ```
- **Ansible 变量**：`interactive_username`（必填）、
  `interactive_ssh_public_key`（可选，来自 inventory group_vars）等。

## 参数与 defaults 对照

`argument_specs` 中的 optional 变量，除 `interactive_ssh_public_key`
（有意不定义，见上）外，其余均已在 `defaults/main.yaml` 定义 ✅。

## 使用范例

本项目在 `playbooks/bootstrap.yaml` 中调用：

```yaml
- name: Set up interactive user
  hosts: interactive
  vars:
    interactive_sudoer: true
    interactive_user_groups:
      - users
  roles:
    - role: interactive_access
```
