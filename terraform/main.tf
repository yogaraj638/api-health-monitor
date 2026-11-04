# ---------- Which tools and which AWS region ----------
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"   # the official AWS plugin for Terraform
      version = "~> 6.0"          # any 6.x version (pin, like requirements.txt)
    }
  }
}

provider "aws" {
  region = var.region             # from variables.tf
}

# ---------- Find the latest Amazon Linux 2023 image (AMI) ----------
# AWS publishes the newest AMI ID here, so we never hard-code an ID that goes stale
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# ---------- Firewall: what traffic may reach the server ----------
resource "aws_security_group" "monitor" {
  name        = "api-health-monitor-sg"
  description = "Allow HTTP to the dashboard"

  ingress {                        # INBOUND rules
    description = "Dashboard (HTTP)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]    # anyone on the internet (it's a public dashboard)
  }
  # No port 22 (SSH) at all: we log in via Session Manager instead (safer)

  egress {                         # OUTBOUND: allow everything
    from_port   = 0                # (server must reach GitHub, Docker Hub, the URLs it checks)
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------- Where container logs go ----------
resource "aws_cloudwatch_log_group" "monitor" {
  name              = "/api-health-monitor"
  retention_in_days = 7            # auto-delete old logs (saves money)
}

# ---------- IAM role: permissions FOR THE SERVER (not for you) ----------
resource "aws_iam_role" "monitor" {
  name = "api-health-monitor-role"
  assume_role_policy = jsonencode({          # "EC2 instances are allowed to use this role"
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Allow logging in from the AWS Console (Session Manager), no SSH keys needed
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.monitor.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Allow sending logs to CloudWatch
resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.monitor.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Wrapper that attaches the role to an EC2 instance
resource "aws_iam_instance_profile" "monitor" {
  name = "api-health-monitor-profile"
  role = aws_iam_role.monitor.name
}

# ---------- The server ----------
resource "aws_instance" "monitor" {
  ami                    = data.aws_ssm_parameter.al2023.value
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.monitor.id]
  iam_instance_profile   = aws_iam_instance_profile.monitor.name

  # Script that runs ONCE on first boot (see user_data.sh)
  user_data = templatefile("${path.module}/user_data.sh", {
    repo_url       = var.repo_url
    region         = var.region
    log_group      = aws_cloudwatch_log_group.monitor.name
    check_interval = var.check_interval
  })
  user_data_replace_on_change = true   # changing the script recreates the server

  tags = {
    Name = "api-health-monitor"        # name shown in the EC2 console
  }
}