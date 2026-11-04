#!/bin/bash
# Runs once, as root, when the EC2 instance first boots.
# ${...} values are filled in by Terraform's templatefile().
set -e                                   # stop at the first error

dnf install -y docker git                # dnf = Amazon Linux's package manager
systemctl enable --now docker            # start Docker now AND on every reboot

git clone ${repo_url} /opt/monitor       # get your code
cd /opt/monitor
docker build -t api-health-monitor .     # same build as on your laptop

docker run -d --name monitor --restart unless-stopped \
  -p 80:8080 \
  -e CHECK_INTERVAL=${check_interval} \
  --log-driver awslogs \
  --log-opt awslogs-region=${region} \
  --log-opt awslogs-group=${log_group} \
  api-health-monitor