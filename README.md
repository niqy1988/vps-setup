# vps-setup
Ansible and configs for VPS setup

Install requirements with
```bash
ansible-galaxy install -r ansible/requirements.yml
```

Setup basic users and ssh login config with
```bash
ansible-playbook ansible/bootstrap/user_login.yaml 
```