# vps-setup
Ansible scripts and configs for VPS setup

`ansible/sample_inventory/` contains a sample inventory with dummy access/account info, you need to replace it with your own inventory

Install requirements with
```bash
ansible-galaxy install -r ansible/requirements.yaml
```

Bootstrap server for future ansible configuration with
```bash
ansible-playbook ansible/bootstrap.yaml 
```

Setup all servers with
```bash
ansible-playbook ansible/all.yaml 
```
