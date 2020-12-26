# Set up interactive access account

> This role requires root access (`become: yes`)

Set up a remote account for interactive shell access

Requires `username` and `password` variables defined separately to run

Default ssh public key is `~/.ssh/id_rsa.pub`, which can be changed with `ssh_public_key_file` variable

By default, the interactive user will be in `sudo` group, which can be overridden by `groups` list