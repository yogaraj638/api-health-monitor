# Settings you can change without editing main.tf (like .env for Terraform)

variable "region" {
  description = "AWS region"
  default     = "ap-south-1"            # Mumbai
}

variable "instance_type" {
  description = "EC2 size"
  default     = "t3.micro"              # small and cheap
}

variable "repo_url" {
  description = "Git repo the server clones"
  default     = "https://github.com/yogaraj638/api-health-monitor.git"
}

variable "check_interval" {
  description = "Seconds between check rounds"
  default     = 60
}

# What Terraform prints after apply
output "dashboard_url" {
  value = "http://${aws_instance.monitor.public_ip}"
}

output "instance_id" {
  value = aws_instance.monitor.id
}