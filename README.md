# vps-setup
Ansible scripts and configs for VPS setup

`sample_inventory/` contains a sample inventory with dummy access/account info, you need to replace it with your own inventory

Install uv and ansible
```shell
# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# install ansible with uv
uv tool install --with "bcrypt<5" --with libpass --with-executables-from ansible-core,ansible-lint ansible
```

Install requirements with
```shell
ansible-galaxy install -r requirements.yaml
```

Bootstrap server for future configuration with
```shell
ansible-playbook bootstrap.yaml 
```

Setup all servers with
```shell
ansible-playbook all.yaml 
```

Debug print local ansible environment with
```bash
ansible-playbook debug_print.yaml 
```