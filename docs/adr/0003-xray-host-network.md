# ADR-003: Xray uses host network mode

- **Status:** Accepted
- **Date:** 2026-06-09
- **Scope:** 适用于全部 `xray` 组主机。原为单机方案，现已全面铺开（2026-08-04）。
- **Context:** Xray needs to support UDP/QUIC protocols. In rootless Podman, UDP port mapping via slirp4netns is unreliable. Running Xray in `host` network mode avoids this limitation entirely.
- **Decision:** Xray runs in `Network=host` (host network mode) Quadlet. It listens on `127.0.0.1`（Xray 入站端口，由 `xray_*_port` 变量配置，示例见 `sample_inventory/`）and receives traffic forwarded by Traefik via the loopback interface. Traefik runs in `podman_network` and routes requests to `127.0.0.1`（Xray 入站端口）.
- **Consequences:**
  - Xray cannot share ports with other services (port conflicts on host)
  - Xray has direct access to host network interfaces
  - Traffic between Traefik and Xray goes through the host's loopback, adding a minor hop
  - Future QUIC support is unblocked without workaround complexity
