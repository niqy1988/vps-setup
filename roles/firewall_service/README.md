# firewall_service 角色

向 `firewalld` 注册一个新的服务（service）。通过模板生成
`/etc/firewalld/services/<service_name>.xml`，再永久启用该服务，使特定
TCP / UDP 端口对防火墙开放。

## 功能概述

1. 用 `service.xml.j2` 渲染 `/etc/firewalld/services/<service_name>.xml`，
   文件中列出所有要开放的 TCP / UDP 端口（`mode: 0644`）。
2. `flush_handlers` 后通过 `ansible.posix.firewalld` 把该服务设为
   `enabled`（`immediate: true` + `permanent: true`）。
3. 变更后通知 handler 重载 `firewalld`。

## 角色参数

来自 `meta/argument_specs.yaml`：

| 变量 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `service_name` | str | ✅ 是 | — | 服务名，也是生成的 XML 文件名 |
| `tcp_ports` | list\[int\] | 否 | `[]` | 要开放的 TCP 端口列表 |
| `udp_ports` | list\[int\] | 否 | `[]` | 要开放的 UDP 端口列表 |

## 依赖项

- **其他 role**：无（不依赖本项目其他 role）。
- **Ansible 变量 / 前置条件**：
  - 目标机需已安装并启动 `firewalld`（由 `playbooks/bootstrap.yaml` 的
    “Initialize firewalld” 阶段完成）。

## 参数与 defaults 对照

`argument_specs` 中所有 optional 变量（`tcp_ports`、`udp_ports`）均已在
`defaults/main.yaml` 中定义 ✅。`service_name` 为必填，无需默认值。

## 使用范例

```yaml
- hosts: all
  roles:
    - role: firewall_service
      service_name: myapp
      tcp_ports:
        - 8080
        - 8443
      udp_ports:
        - 5353
```

也可作为普通任务（`include_role`）使用：

```yaml
- hosts: all
  tasks:
    - name: 开放 myapp 端口
      ansible.builtin.include_role:
        name: firewall_service
      vars:
        service_name: myapp
        tcp_ports: [8080]
```
