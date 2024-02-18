# Create/modify new user

> This role requires root access (`become: true`)

Set up a remote account for interactive shell access

Requires `username` and `password` variables defined separately to run

Default ssh public key is `~/.ssh/id_rsa.pub`, which can be changed with `ssh_public_key_file` variable

Default user group is the same as username, which can be overriden with `user_groups` list variable

Whether user has sudo access is controlled by `sudoer` variable (default: `no`)
