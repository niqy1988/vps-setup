# Set up interactive access account

> This role requires root access (`become: yes`)

Set up a remote account for interactive shell access

Requires `interactive.username` and `interactive.password` variables defined separately to run

Default ssh public key is `~/.ssh/id_rsa.pub`, which can be changed with `interactives.sh_public_key_file` variable

By default, the interactive user will be in `sudo` group, which can be overridden by `interactive.groups` list