# rclone

Deploy rootless [rclone](https://rclone.org/) mounts as user systemd template
instances (`rclone@<remote>`).

## Behaviour

This role is a **pure executor**: it takes one input, `rclone_mounts`, and
deploys exactly what it is given. It does not merge, override or resolve any
configuration; `vfs_cache_size` is treated as the **final** value. How that
final value is computed (defaults, group/host overrides, multi-group union) is
decided by the caller (e.g. in the playbook that invokes this role).

For each item in `rclone_mounts` it:
1. writes the remote config block into `~/.config/rclone/rclone.conf` using
   `blockinfile` (marker `# {mark} ANSIBLE MANAGED BLOCK: <name>.conf`, one
   unique block per mount),
2. writes `~/.config/rclone/mounts/<name>.env` with:
   - `RCLONE_VFS_CACHE_MODE` (default `full`; `off|minimal|writes|full`),
   - `RCLONE_VFS_CACHE_MAX_SIZE` (default `off` = unlimited),
   - `RCLONE_VFS_CACHE_MIN_FREE_SPACE` (default `off` = unlimited),
3. ensures `rclone@<name>` user service is enabled and started.

For mounts listed in `rclone_removed_mounts` it stops/disables the service,
removes the config block and the env file.

The vfs cache settings are provided to the mount via an env file (not encoded
in the service instance name), so multiple mounts never collide and a change
only restarts the affected service.

## Inputs

| Variable | Default | Description |
| --- | --- | --- |
| `rclone_mounts` | `[]` | list of `{name, vfs_cache_size}` to deploy. `name` must match `inventory/rclone/conf.d/<name>.conf`. Per-item `vfs_cache_mode` (default `full`), `vfs_cache_size` (default `off` = unlimited) and `vfs_cache_min_free_space` (default `off` = unlimited) are supported. |
| `rclone_removed_mounts` | `[]` | Mount names whose service is stopped/disabled and whose config block + env file are removed. |
| `rclone_conf_src_dir` | `inventory/rclone/conf.d` | Controller-side directory with one `.conf` per remote (sensitive tokens; keep out of VCS). |
| `rclone_user` | `rclone_user` | User running the rootless mounts. |
| `rclone_uid` | `600000` | UID/GID of the rclone user. |
| `rclone_mount_base` | `/mnt/rclone` | Base directory of mount points. |

## Source config layout

Each remote has its own INI file under `inventory/rclone/conf.d/`
(git-ignored). A file may contain several sections, e.g. `pcloud.conf`
containing both `[pcloud_raw]` and `[pcloud]` (crypt layer). rclone resolves
remote references after loading the whole config, so section order does not
matter.

## Example caller

```yaml
- hosts: dev
  roles:
    - role: rclone
```
with `rclone_mounts` provided by the caller (computed from group/host
variables, defaults, or a single explicit value).
