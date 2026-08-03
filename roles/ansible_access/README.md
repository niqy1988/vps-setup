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

Consider setting up the same account as default in `ansible.cfg` as follows
(no private key file is specified anywhere in this project; authentication is
left to OpenSSH's automatic key discovery — keys from your local ssh agent, or
private keys at default locations like `~/.ssh/id_ed25519`, will be tried):
```ini
[defaults]
remote_user = ansible_remote
```
