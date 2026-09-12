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
```
