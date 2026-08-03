# Set up interactive access account

> This role requires root access (`become: true`)

Set up a remote account for interactive shell access

Requires `username` and `password` variables defined separately to run

The ssh public key is provided as text (e.g. `ssh-ed25519 AAAA...`), not a file path; set it with the `interactive_ssh_public_key` variable

Default user group is the same as username, which can be overriden with `user_groups` list variable

Whether user has sudo access is controlled by `sudoer` variable (default: `no`)
