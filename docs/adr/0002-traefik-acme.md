# ADR-002: Traefik ACME for certificate management

- **Status:** Accepted
- **Date:** 2026-06-09
- **Scope:** 适用于全部 `xray` 组主机。原为单机方案，现已全面铺开（2026-08-04）。
- **Context:** The existing `acme` role uses `acme.sh` to obtain certificates and places them in `/app/certs/`. This adds a separate tool to manage alongside Podman services.
- **Decision:** Replace `acme.sh` with Traefik's built-in ACME client using Cloudflare DNS challenge. Certificates are stored as `acme.json` in Traefik's config directory.
- **Consequences:**
|  - One less external tool to maintain
|  - Traefik manages its own certificates automatically (renewal handled by Traefik)
|  - Other services no longer need to read certificate files — Traefik terminates TLS and forwards HTTP
|  - `acme.json` is persisted via a bind mount volume, defined in the same `podman_container` `state: quadlet` module call as the Traefik container
|  - The `acme/` role has been removed (2026-08-04) — it was unused, and Traefik now fully owns certificate management
