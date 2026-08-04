# ansible_access 角色

设置一个供 Ansible 远程连接的 sudoer 账号（本项目默认 `ansible_remote`），
并初始化 `/etc/ansible` 与 `/etc/ansible/facts.d` 目录（供各 role 持久化
本地 facts，如 `wgcf` 角色写入 `wgcf.fact`）。

## 功能概述

1. 通过依赖的 [`user`](../user/README.md) 角色创建 sudoer 用户。
2. 创建 `/etc/ansible` 目录（属主 root）。
3. 创建 `/etc/ansible/facts.d` 目录（属主为 `ansible_username`，供
   `wgcf` 等角色写本地 fact 文件）。
4. `reset_connection` 重置 SSH 连接使变更立即生效。

## 角色参数

本角色**没有** `meta/argument_specs.yaml`（仅 `meta/main.yaml` 声明依赖），
参数直接来自 `defaults/main.yaml` 与 inventory 变量：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `ansible_username` | str | 否 | `ansible_remote` | Ansible 远程用户名 |
| `ansible_uid` | int | 否 | `900000` | 远程用户 UID/GID |
| `ansible_ssh_public_key` | str | 否 | **无默认**（见下） | SSH 公钥文本，用于登录 |

> ⚠️ `ansible_ssh_public_key` **未在 `defaults/main.yaml` 定义**——
> 属有意为之，应在 inventory 中设置
> （示例见 `sample_inventory/group_vars/all/credentials.yaml`）。

## 依赖项

- **其他 role**：依赖 [`user`](../user/README.md) 角色（见
  `meta/main.yaml`），调用方式：
  ```yaml
  dependencies:
    - role: user
      username: "{{ ansible_username }}"
      uid: "{{ ansible_uid }}"
      user_groups: []
      ssh_public_key: "{{ ansible_ssh_public_key }}"
      sudoer: true
      comment: ansible remote user
  ```
- **Ansible 变量**：`ansible_username`、`ansible_uid`、
  `ansible_ssh_public_key`（后两者来自 inventory group_vars）。

## 使用范例

本项目在 `playbooks/bootstrap.yaml` 中直接调用：

```yaml
- name: Set up ansible remote user
  hosts: all
  vars:
    ansible_user: "{{ bootstrap_username | default('root') }}"
  roles:
    - role: ansible_access
```

之后可在 `ansible.cfg` 中把默认远程用户设为该账号：

```ini
[defaults]
remote_user = ansible_remote
```

> 本项目不指定任何私钥文件，认证交给 OpenSSH 自动密钥发现（本地 ssh
> agent 或默认位置的私钥如 `~/.ssh/id_ed25519`）。
