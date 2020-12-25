# vps-setup
Ansible and configs for VPS setup

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