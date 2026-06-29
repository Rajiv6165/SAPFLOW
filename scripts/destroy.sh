#!/bin/bash
echo "⚠️  This will destroy ALL SAPFlow AWS resources and cannot be undone."
read -p "Type 'destroy' to confirm: " confirm
if [ "$confirm" != "destroy" ]; then
  echo "Cancelled."
  exit 1
fi
cd infra/terraform
terraform destroy -auto-approve
echo "✅ All resources destroyed."
