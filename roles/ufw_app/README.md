# ufw_app 角色

通过 `ufw` 开放指定 TCP / UDP 端口。防火墙本身由
`playbooks/bootstrap.yaml` 的 “Initialize ufw” 阶段初始化
（默认拒绝入站、放行 SSH）。

## 功能概述

1. 在 `/etc/ufw/applications.d/ufw-custom` 中生成应用规则
   （`community.general.ini_file`，含 title / description / ports）；
2. 通过 `community.general.ufw` 放行对应的应用规则；
3. 规则即时生效，无需重载防火墙。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `ufw_app_name` | str | ✅ 是 | — | 应用名，用作 ufw-custom 规则 section 名与任务名 |
| `ufw_app_description` | str | 否 | `Custom application` | 应用描述（写入 ufw-custom 规则） |
| `ufw_app_ports` | dict | 否 | `{}` | 要开放的端口，键为协议（`tcp` / `udp`），值为端口或端口区间字符串列表（如 `80`、`"9000:9010"`） |

## 依赖项

- **其他 role**：无（不依赖本项目其他 role）。
- **Ansible 变量 / 前置条件**：
  - 目标机需已安装并启用 `ufw`（由 `playbooks/bootstrap.yaml` 的
    “Initialize ufw” 阶段完成）。

## 参数与 defaults 对照

`argument_specs` 中所有 optional 变量（`ufw_app_description`、`ufw_app_ports`）均已在
`defaults/main.yaml` 中定义 ✅。`ufw_app_name` 为必填，无需默认值。

## 使用范例

```yaml
- hosts: all
  roles:
    - role: ufw_app
      ufw_app_name: myapp
      ufw_app_description: ufw rule for myapp
      ufw_app_ports:
        tcp:
          - 8080
          - "9000:9010"
        udp:
          - 8443
```

也可作为普通任务（`include_role`）使用：

```yaml
- hosts: all
  tasks:
    - name: 开放 myapp 端口
      ansible.builtin.include_role:
        name: ufw_app
      vars:
        ufw_app_name: myapp
        ufw_app_description: ufw rule for myapp
        ufw_app_ports:
          tcp:
            - 8080
            - "9000:9010"
          udp:
            - 8443
```
