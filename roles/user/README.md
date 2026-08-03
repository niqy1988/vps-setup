# Create/modify new user

> This role requires root access (`become: true`)

Set up a user account on the target machine

Requires `username` and `comment` variables defined separately to run

either `password` or `ssh_public_key_file` has to be set, or there's no way to login as the user

Default user group is the same as username
additional user groups can be added with `user_groups` list variable

Whether user has sudo access is controlled by `sudoer` variable (default: `false`)
