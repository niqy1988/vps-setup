# Set up ansible remote user

> This role requires root access (`become: true`)

Set up a remote sudoer account for ansible to connect to

Valid variables and default values:
|Variable            |Default Value             |
|--------------------|--------------------------|
|username            |ansible_remote            |
|uid                 |900000                    |
|ssh_public_key      |<public key as text>      |

The ssh public key is provided as text (e.g. `ssh-ed25519 AAAA...`), not a file path.

Consider setting up the same account as default in `~/.ansible.cfg` as follows:
```ini
[defaults]
remote_user      = ansible_remote
private_key_file = ~/.ssh/ansible_id_rsa
```
