# user 角色（基础角色）

在目标机上创建 / 修改一个用户账号。本角色是**底层基础角色**，被
`ansible_access`、`interactive_access`、`podman`、`rclone` 等多个角色
作为依赖调用；也可单独直接调用。

## 功能概述

1. 创建同名的用户组（gid = `uid`）并创建用户（shell `/bin/bash`，
   创建 home 目录）。
2. 设置 `/etc/subuid` / `/etc/subgid` 映射（`username:<uid+1>:65535`），
   供 rootless 容器使用。
3. 创建 `~/.ansible/tmp` 目录。
4. SSH 公钥：设置 `ssh_public_key` 则写入 `authorized_keys`
   （`exclusive: true`）；未设置则删除 `authorized_keys`（禁止 SSH 登录）。
5. Linger（`linger: true`）：启用 `loginctl enable-linger`，并在
   `.bashrc` 中导出 `XDG_RUNTIME_DIR` / `DBUS_SESSION_BUS_ADDRESS`，
   保证用户级 systemd 服务开机自启；`linger: false` 时反向撤销。
6. sudo：`sudoer: true` 时写入 `/etc/sudoers.d/<username>`（有密码则
   需输入密码，无密码则 `NOPASSWD:ALL`）；否则删除该文件。

## 角色参数

来自 `meta/argument_specs.yaml`（注意：作为底层角色，参数使用**通用名**，
不带 role 前缀）：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `username` | str | ✅ 是 | — | 用户名 |
| `comment` | str | ✅ 是 | — | 账号描述 |
| `password` | str | 否 | **无默认**（见下） | 密码（`no_log`）；缺省 = 账号锁定 |
| `ssh_public_key` | str | 否 | **无默认**（见下） | SSH 公钥文本（非文件路径）；缺省 = 无 SSH 登录 |
| `uid` | int | 否 | `100000` | 用户 UID/GID |
| `user_groups` | list\[str\] | 否 | `["users"]` | 额外用户组 |
| `sudoer` | bool | 否 | `false` | 是否授予 sudo 权限 |
| `linger` | bool | 否 | `false` | 是否启用 linger（systemd 用户级服务自启） |

> ⚠️ **`password` 与 `ssh_public_key` 均未在 `defaults/main.yaml` 定义**
> ——这是**有意设计**：`password` 缺省表示“锁定账号”，`ssh_public_key`
> 缺省表示“禁止 SSH 登录”。`username`、`comment` 为必填，亦无需默认值。

## 依赖项

- **其他 role**：无（本角色不依赖其他 role，是依赖链的最底层）。
- **Ansible 变量 / 前置条件**：
  - `user_groups` 中引用的组需存在（本项目在 bootstrap 中创建了
    `users` 组；`podman` 依赖本角色时传入 `systemd-journal`）。

## 参数与 defaults 对照

`argument_specs` 中的 optional 变量 `password`、`ssh_public_key`
**有意不在 defaults 定义**（见上，语义为“缺省即禁用”）；其余 optional
变量（`uid`、`user_groups`、`sudoer`、`linger`）均已在 `defaults/main.yaml`
定义 ✅。

## 使用范例

### 直接调用

```yaml
- hosts: all
  roles:
    - role: user
      username: alice
      comment: alice's account
      uid: 100001
      user_groups:
        - users
      sudoer: true
      ssh_public_key: "<ssh_public_key>"
      linger: true
```

只建账号、密码登录（不设 SSH 公钥）：

```yaml
    - role: user
      username: bob
      comment: bob's account
      password: "s3cret"
```

### 作为依赖被其他 role 调用

`ansible_access`（sudoer 远程账号）：

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

`podman`（rootless 容器用户，启用 linger）：

```yaml
dependencies:
  - role: user
    username: "{{ podman_username }}"
    uid: "{{ podman_uid }}"
    user_groups:
      - systemd-journal
      - users
    linger: true
    comment: podman user
```

`rclone`（rclone 挂载用户，启用 linger）与 `interactive_access`
（交互用户）同理，直接使用这些角色即可自动拉起本角色。
