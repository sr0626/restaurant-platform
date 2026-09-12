output "schedule_arn" {
  description = "EventBridge Scheduler schedule ARN"
  value       = aws_scheduler_schedule.deal_expiry.arn
}

output "scheduler_role_arn" {
  description = "IAM role ARN used by EventBridge Scheduler to invoke the Lambda"
  value       = aws_iam_role.scheduler.arn
}
