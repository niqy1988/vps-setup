# ADR-001: Use Quadlet instead of podman_container module

- **Status:** Accepted
- **Date:** 2026-06-09
- **Updated:** 2026-06-10 (refined for `state: quadlet` module calls)
- **Scope:** 适用于全部 `xray` 组主机。原为单机方案，现已全面铺开（2026-08-04）。
- **Context:** Podman services can be managed either via the `containers.podman.podman_container` Ansible module with `state: present` (imperative, starts containers on the host) or via Quadlet `.container` definition files (declarative, managed by systemd). Newer versions of the `containers.podman` collection support `state: quadlet`, which generates `.container` / `.network` / `.volume` definition files without starting any containers on the host.
- **Decision:** Use `containers.podman.podman_container` (and related modules like `podman_network`, `podman_volume`) with `state: quadlet` to generate Quadlet definition files. Ansible tasks pass structured parameters (image, network, healthcheck, labels, volumes...) directly to the modules; the modules render these into `.container`, `.network`, `.volume` files in `~/.config/containers/systemd/`. Trigger `systemctl --user daemon-reload` and `enable --now` after generation.
- **Consequences:**
  - Service lifecycle is managed by systemd user sessions, consistent with Podman's rootless best practices
  - No J2 templates or `template` module — module parameters are typed, documented, and validate at playbook time
  - `argument_specs.yaml` maps directly to module fields, serving as both API docs and defaults
  - Multiple resources (container + network + volume) can be generated in a single task block
  - Rollback requires `systemctl --user disable --now` and cleanup of generated definition files
  - Future containers (e.g. Nextcloud) follow the same pattern — `state: quadlet` generates `.container` files with labels, without requiring new J2 templates
  - Requires relatively recent `containers.podman` collection version
