# wgcf 角色

注册 Cloudflare WARP（Zero Trust）设备并生成 WireGuard 密钥对与设备配置，
最终产出一段可供 Xray 使用的 WireGuard outbound 配置（`wgcf_xray_config`），
并持久化到本机 facts 目录以便幂等复用。

## 功能概述

1. 安装 `wireguard-tools`（`wg` 命令）。
2. 若无已存密钥，生成 WireGuard 私钥 / 公钥（基于
   `ansible_local.wgcf` 事实判断是否已生成）。
3. 生成 12 位随机序列号（`wgcf_serial_number`）。
4. 若本机尚无设备注册信息，通过 Cloudflare Access Service Auth 登录
   WARP API 并注册新设备（设备名 = `inventory_hostname`）。
5. 组装 WireGuard 配置（`wgcf_xray_config`，tag `wgcf_v6`，含 IPv6/IPv4
   地址、peer 端点、reserved 字段等），供 Xray 作 wireguard outbound。
6. 将 `wg_private_key` / `wg_public_key` / `wgcf_serial_number` /
   `wgcf_device_reg` / `wgcf_xray_config` 写入
   `/etc/ansible/facts.d/wgcf.fact`，并重载 facts——后续运行直接读取
   `ansible_local.wgcf.*`，不会重复注册设备。

## 角色参数

来自 `meta/argument_specs.yaml`（**全部必填**）：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `wgcf_organization_name` | str | ✅ 是 | — | Cloudflare Zero Trust 组织名 |
| `wgcf_service_auth_client_id` | str | ✅ 是 | — | 有设备注册权限的 Service Auth Client ID |
| `wgcf_service_auth_client_secret` | str | ✅ 是 | — | Service Auth Secret |

## 依赖项

- **其他 role**：无 `meta/main.yaml` 依赖；但**运行前提**是
  [`ansible_access`](../ansible_access/README.md) 已创建
  `/etc/ansible/facts.d` 目录（facts 持久化依赖），否则写
  `/etc/ansible/facts.d/wgcf.fact` 会失败。
- **Ansible 变量 / facts**：
  - `ansible_local.wgcf.*`：由本角色之前运行写入的事实（私钥、公钥、
    序列号、设备注册信息、xray 配置）。
  - `inventory_hostname`、`ansible_distribution_version`、
    `ansible_distribution`、`ansible_fqdn`：用于设备注册请求体。
  - 自定义 Jinja2 filter：`url_query`、`decode_wgcf_reserved`
    （`filter_plugins/wgcf_filters.py`）。

## 参数与 defaults 对照

所有参数均为 `required: true`，无 optional 变量；该 role **没有
`defaults/main.yaml`**，符合预期 ✅。

## 使用范例

```yaml
- hosts: xray
  roles:
    - role: wgcf
      wgcf_organization_name: myorg
      wgcf_service_auth_client_id: xxxx.access
      wgcf_service_auth_client_secret: "xxxxx"
```

作为其他角色的依赖：`xray` 在 `meta/main.yaml` 中声明
`dependencies: - role: wgcf`，运行 `xray` 角色时先自动注册 WARP 设备，
Xray 的 wireguard outbound（`51_outbound_wgcf.json.j2`）即可读取
`ansible_local.wgcf.wgcf_xray_config`。
