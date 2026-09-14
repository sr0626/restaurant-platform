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

## 2026-09-13
```bash
git push -u origin integration/phase1-backend-full   # claude
git push -u origin feature/phase1-frontend-scaffold   # claude
git push -u origin infra/service-name-and-state-key   # claude
git push -u origin infra/lambda-cognito-listusers   # claude
gh pr create --base main --head integration/phase1-backend-full   # claude
gh pr create --base main --head feature/phase1-frontend-scaffold   # claude
gh pr create --base main --head infra/service-name-and-state-key   # claude
gh pr create --base main --head infra/lambda-cognito-listusers   # claude
```

## 2026-09-13
```bash
git push -u origin docs/project-status   # claude
gh pr create --base main --head docs/project-status   # claude
git push origin integration/phase1-backend-full   # claude  (id/slug fix, commit 1af489d, onto PR #7)
git push origin docs/project-status   # claude  (STATUS.md refresh + .gitignore fix, onto PR #13)
git push origin pr7-slug-test-fix:integration/phase1-backend-full   # claude  (Architect's slug-lookup test coverage, onto PR #7)
git push origin docs/project-status   # claude  (PR #7 approved status update, onto PR #13)
git push origin docs/project-status   # claude  (log entry only, onto PR #13)
git push -u origin docs/relax-feature-branch-push-gate   # claude  (no pre-approval needed, per new rule)
gh pr create --base main --head docs/relax-feature-branch-push-gate   # claude  (no pre-approval needed, per new rule)
```

## 2026-09-13
```bash
git push -u origin docs/project-status   # claude
gh pr create --base main --head docs/project-status   # claude
git push origin integration/phase1-backend-full   # claude  (id/slug fix, commit 1af489d, onto PR #7)
git push origin docs/project-status   # claude  (STATUS.md refresh + .gitignore fix, onto PR #13)
git push origin pr7-slug-test-fix:integration/phase1-backend-full   # claude  (Architect's slug-lookup test coverage, onto PR #7)
git push origin docs/project-status   # claude  (PR #7 approved status update, onto PR #13)
git push -u origin docs/homepage-direction-spice-market   # claude  (no pre-approval needed, per relaxed push rule)
gh pr create --base main --head docs/homepage-direction-spice-market   # claude  (no pre-approval needed, per relaxed push rule)
git push -u origin docs/merge-hygiene-rule   # claude
gh pr create --base main --head docs/merge-hygiene-rule   # claude
git push -u origin feature/homepage-spice-market-theme   # claude  (Spice Market homepage implementation, no pre-approval needed, per relaxed push rule)
gh pr create --base main --head feature/homepage-spice-market-theme   # claude  (no pre-approval needed, per relaxed push rule)
git push -u origin docs/status-homepage-merged   # claude
gh pr create --base main --head docs/status-homepage-merged   # claude
git push -u origin fix/next-config-js   # claude  (next.config.ts -> .mjs fix, no pre-approval needed, per relaxed push rule)
gh pr create --base main --head fix/next-config-js   # claude  (no pre-approval needed, per relaxed push rule)
git push -u origin feature/search-and-restaurant-detail-pages   # claude  (search + restaurant detail pages, no pre-approval needed, per relaxed push rule)
gh pr create --base main --head feature/search-and-restaurant-detail-pages   # claude  (no pre-approval needed, per relaxed push rule)
git push -u origin docs/api-contracts-restaurants-list-cuisine-tags   # claude  (no pre-approval needed, per relaxed push rule)
gh pr create --base main --head docs/api-contracts-restaurants-list-cuisine-tags   # claude  (no pre-approval needed, per relaxed push rule)
gh pr ready 21 --undo   # claude  (converted PR #21 to draft, per new draft-until-approved rule)
git push -u origin docs/draft-pr-until-architect-approves   # claude
gh pr create --base main --head docs/draft-pr-until-architect-approves   # claude
git merge origin/main   # claude  (resolved next.config.ts/.mjs + CMD_LOG.md conflicts from PR #19 landing after this branch was cut)
git push origin feature/search-and-restaurant-detail-pages   # claude  (Architect fix-loop: merge main to un-revert the next.config.mjs fix, onto PR #21)
git merge origin/main   # claude  (resolved second CMD_LOG.md conflict — PR #20 merged to main mid-review)
git push origin feature/search-and-restaurant-detail-pages   # claude  (onto PR #21)
git push -u origin feature/restaurants-list-and-cuisine-tags   # claude  (Gap A/B endpoint implementation, no pre-approval needed, per relaxed push rule)
gh pr create --base main --head feature/restaurants-list-and-cuisine-tags   # claude  (no pre-approval needed, per relaxed push rule)
git merge origin/main   # claude  (resolved CMD_LOG.md conflict — PR #22 merged mid-review, onto PR #21)
git push origin HEAD:feature/search-and-restaurant-detail-pages   # claude  (onto PR #21)
git push -u origin feature/login-cognito-signin   # claude  (real Cognito sign-in flow, no pre-approval needed, per relaxed push rule)
gh pr create --draft --base main --head feature/login-cognito-signin   # claude  (opened as draft, per draft-until-Architect-approval rule)
```
