---
name: opentofu-plan-and-validation
description: Validates, lints, and generates execution plans for OpenTofu/Terraform infrastructure modules without applying destructive changes.
---

# OpenTofu Plan and Validation Procedure

1. Read infrastructure specification and target cloud provider requirements.
2. Author modular Terraform/OpenTofu code in `terraform/modules/`.
3. Format configuration: `tofu fmt -check`.
4. Validate syntax and configuration integrity: `tofu validate`.
5. Run static security and best-practice linting: `tflint`.
6. Generate speculative execution plan: `tofu plan -no-color -out=tfplan`.
7. Review plan output to ensure zero unintended resource deletions.
8. Output plan summary and submit PR for human/executive approval.
