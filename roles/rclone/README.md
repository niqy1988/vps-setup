# rclone 角色

以 rootless 方式部署 [rclone](https://rclone.org/) 挂载，每个远端一个
用户级 systemd 模板实例（`rclone@<remote>`）。

## 功能概述

本角色是**纯执行者**：唯一输入 `rclone_mounts`，按给定内容精确部署，
**不做任何合并 / 覆盖 / 解析**——`vfs_cache_size` 等被视为**最终值**。
最终值如何得出（默认、组/主机覆盖、多组合并）由调用方（如调用本角色
的 playbook）决定。

对 `rclone_mounts` 中的每一项，本角色会：

1. 用 `blockinfile` 把远端配置块写入 `~/.config/rclone/rclone.conf`
   （marker `# {mark} ANSIBLE MANAGED BLOCK: <name>.conf`，每个挂载一个
   独立块）；
2. 写入 `~/.config/rclone/mounts/<name>.env`：
   - `RCLONE_VFS_CACHE_MODE`（默认 `full`；`off|minimal|writes|full`），
   - `RCLONE_VFS_CACHE_MAX_SIZE`（默认 `off` = 不限），
   - `RCLONE_VFS_CACHE_MIN_FREE_SPACE`（默认 `off` = 不限）；
3. 确保 `rclone@<name>` 用户服务已启用并启动。

对 `rclone_removed_mounts` 中的名字：停止 / 禁用服务、删除配置块与
env 文件。

vfs 缓存参数通过 env 文件传给挂载（而不是编码进服务实例名），因此多个
挂载互不冲突，且修改只会重启受影响的那个服务。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `rclone_mounts` | list\[dict\] | 否 | `[]` | 要部署的挂载列表（子项见下） |
| `rclone_removed_mounts` | list\[str\] | 否 | `[]` | 要移除的挂载名（停服务 + 删配置块 + 删 env 文件） |
| `rclone_conf_src_dir` | str | 否 | `{{ inventory_dir }}/rclone/conf.d`（defaults 默认值，可覆盖） | 控制端存放各远端 `.conf` 的目录（含敏感 token 勿入库，示例见 `sample_inventory/rclone/conf.d/`）；基于 `inventory_dir` 解析，不受 playbook 位置影响 |
| `rclone_user` | str | 否 | `rclone_user` | 运行 rootless 挂载的用户 |
| `rclone_uid` | int | 否 | `600000` | rclone 用户 UID/GID |
| `rclone_mount_base` | str | 否 | `/mnt/rclone` | 挂载点基础目录 |

`rclone_mounts` 子项（argument_specs 嵌套校验）：

| 子变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `name` | str | ✅ 是 | — | 远端名，须匹配 `rclone_conf_src_dir` 下 `<name>.conf`（示例见 `sample_inventory/rclone/conf.d/`） |
| `vfs_cache_mode` | str | 否 | `full`（实际来自模板） | `off\|minimal\|writes\|full` |
| `vfs_cache_size` | str | 否 | `off`（实际来自模板） | VFS 缓存上限（如 `2G`）；`"off"` = 不限 |
| `vfs_cache_min_free_space` | str | 否 | `off`（实际来自模板） | 保留的最小剩余空间（如 `1G`）；`"off"` = 不限 |

> ⚠️ **`off` 必须加引号**：YAML 1.1 会把裸 `off` 解析成布尔 `false`，
> 要表示“不限”请写 `"off"`。

## 依赖项

- **其他 role**：依赖 [`user`](../user/README.md) 角色（见
  `meta/main.yaml`），创建 rclone 挂载用户（`linger: true`）：
  ```yaml
  dependencies:
    - role: user
      username: "{{ rclone_user }}"
      uid: "{{ rclone_uid }}"
      user_groups: [users]
      linger: true
      comment: rclone mount user
  ```
- **Ansible 变量 / 前置条件**：
  - `rclone_user` / `rclone_uid`：如需让 rclone 复用 Podman 用户，在
    inventory 中设置 `rclone_user: "{{ podman_username }}"` /
    `rclone_uid: "{{ podman_uid }}"`（示例见 `sample_inventory/`），
    使挂载与容器共享同一用户环境（避免独立 rclone 用户导致 systemd
    user 实例缺 podman 已配好的环境而启动失败）。
  - 每个远端一个源配置文件放 `rclone_conf_src_dir` 指定的目录下
    （示例见 `sample_inventory/rclone/conf.d/`；一个文件可含多个
    section，如 `[<name>_raw]` + `[<name>]` crypt 层，section 顺序
    无关）。

## 参数与 defaults 对照

`argument_specs` 中所有顶层 optional 变量均已在 `defaults/main.yaml`
定义 ✅。嵌套子项 `vfs_cache_mode` / `vfs_cache_size` /
`vfs_cache_min_free_space` 为可选且无 spec 默认，**实际默认值来自
`templates/vfs_cache.env.j2` 的 `| default(...)`**（`full` / `"off"` /
`"off"`），符合“纯执行者、默认由模板兜底”的设计。

## 源配置布局

每个远端一个 INI 文件放 `rclone_conf_src_dir` 指定的目录（示例见
`sample_inventory/rclone/conf.d/`）。一个文件可含多个 section（如
`<remote>.conf` 含 `[<remote>_raw]` 与 `[<remote>]` crypt 层）。rclone
在加载完整个配置后才解析远端引用，因此 section 顺序不影响。

## 消费类角色（如 `filebrowser`）的使用方式

`filebrowser` 等"消费 rclone 挂载"的角色只声明所需挂载的**名称列表**
（如 `filebrowser_rclone_mounts: [mydrive]`），挂载的**完整配置**统一
在 host vars 的共享变量 `rclone_mounts` 中定义（本角色的唯一输入）。
本角色被这类角色依赖时直接读取 host vars 的 `rclone_mounts` 部署，
不做合并 / 过滤；消费角色仅按名称在自身数据根（如 `/data/<name>`）
建符号链接暴露。示例见 `roles/filebrowser/README.md` 与 `sample_inventory/`。

## 使用范例

```yaml
- hosts: dev
  roles:
    - role: rclone
      rclone_mounts:
        - name: mydrive
          vfs_cache_mode: full
          vfs_cache_size: "2G"
          vfs_cache_min_free_space: "1G"
        - name: otherdrive
          vfs_cache_size: "off"
```

清理不再需要的挂载：

```yaml
    - role: rclone
      rclone_removed_mounts:
        - old_drive
```

