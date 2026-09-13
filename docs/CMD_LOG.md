# Command Log

Every `git push`, AWS CLI/SDK command, and `terraform plan`/`apply` — in
execution order, grouped by date. `# user` / `# claude` marks who ran it.

## 2026-09-12
```bash
git push origin main   # claude
git push origin main   # claude
git push origin main   # claude
aws configure sso --profile restaurant-platform-dev   # user
aws sts get-caller-identity --profile restaurant-platform-dev   # user
aws s3 mb s3://restaurant-platform-tfstate-sr0626 --region us-east-1   # user
aws s3api put-bucket-versioning --bucket restaurant-platform-tfstate-sr0626 --versioning-configuration Status=Enabled   # user
aws dynamodb create-table --table-name restaurant-platform-tfstate-lock --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region us-east-1   # user
aws s3api get-bucket-versioning --bucket restaurant-platform-tfstate-sr0626   # user
aws dynamodb describe-table --table-name restaurant-platform-tfstate-lock --query "Table.TableStatus" --output text   # user
git push origin main   # claude
git push -u origin feature/phase1-architect-schema   # claude
git push -u origin infra/ecr-container-lambda-image   # claude
git push -u origin devops/ci-pipeline-placeholder   # claude
gh pr create --base main --head feature/phase1-architect-schema   # claude
gh pr create --base main --head infra/ecr-container-lambda-image   # claude
gh pr create --base main --head devops/ci-pipeline-placeholder   # claude
gh api --method PUT repos/sr0626/restaurant-platform/branches/main/protection --input branch_protection.json   # claude
git push origin infra/ecr-container-lambda-image   # claude
git push -u origin docs/environment-promotion-strategy   # claude
gh pr create --base main --head docs/environment-promotion-strategy   # claude
git push origin main   # claude  (rejected — main is now protected, no direct pushes)
git push -u origin docs/cmd-log-updates   # claude
gh pr create --base main --head docs/cmd-log-updates   # claude
git merge origin/main   # claude  (resolved devops/CLAUDE.md add/add conflict on docs/environment-promotion-strategy)
git push origin docs/environment-promotion-strategy   # claude
git merge main   # claude  (resolved architect/CLAUDE.md add/add conflict on docs/architect-approval-gate)
git push -u origin docs/architect-approval-gate   # claude
gh pr create --base main --head docs/architect-approval-gate   # claude
```
