---
name: iam-least-privilege-audit
description: Scans Terraform IAM policies and AWS environments for excessive permissions, wildcards, and unencrypted storage.
---

# IAM Least Privilege Audit Procedure

1. Read Terraform infrastructure definitions in `terraform/`.
2. Run automated static IaC security scanner: `checkov -d terraform/` and `tfsec terraform/`.
3. Check for critical misconfigurations:
   - IAM statements with `Effect: Allow` and `Action: "*"`.
   - S3 buckets without `block_public_acls: true` or KMS encryption.
   - Security groups with `0.0.0.0/0` ingress on ports other than 80/443.
4. Execute secret leak scan: `gitleaks detect --verbose`.
5. Author Cloud Security Audit Report in `docs/security/cloud/`.
6. Provide remediated, minimal IAM policy JSON.
