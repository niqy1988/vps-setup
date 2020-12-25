# Set up ansible remote user

> This role requires root access (`become: yes`)

Set up a remote sudoer account for ansible to connect to

Consider setting up the same account as default in `~/.ansible.cfg` as follows:
```cfg
[defaults]
remote_user      = ansible_remote_user
private_key_file = ~/.ssh/id_rsa.pub
```
