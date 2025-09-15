# this code intend to automate task assign in review for people who didn't annotated it.
from encord import EncordUserClient # type: ignore
import pandas as pd
import random

# Confirm SDK has required method

# Authenticate using encord API key
client = EncordUserClient.create_with_api_key(
    json_credentials_path="encord_api_key.json"
)
# using ssh private key instead
#client = EncordUserClient.create_with_ssh_private_key()

#  Load night Encord project (statrted on night project)
project = client.get_project("28a20d28-376e-474b-939a-97b55f36bf60")

#  Get all label rows
label_rows = project.get_label_rows_v2()

#  Get current user 
current_user = client.get_user()

# Get all project users 
project_users = project.get_project_users()
reviewers = [
    user for user in project_users
    if user.get("email")  # Optional: Add role check if needed
]

#  Assign reviewers (avoiding self-review)
assigned = []
skipped = []

for label_hash, data in label_rows.items():
    status = data.get("label_status")
    if status != "LABELLED":
        continue

    annotator_email = data.get("dataset_row", {}).get("created_by", "")
    current_reviewer = data.get("last_edited_by", "")

    if annotator_email == current_reviewer:
        continue  # Already reviewed by same person — skip

    eligible_reviewers = [
        r for r in reviewers if r["email"] != annotator_email
    ]

    if not eligible_reviewers:
        skipped.append({
            "label_hash": label_hash,
            "annotator_email": annotator_email,
            "reason": "No eligible reviewers"
        })
        continue

    selected_reviewer = random.choice(eligible_reviewers)

    try:
        project.assign_reviewer_to_label_row(
            label_hash=label_hash,
            user_id=selected_reviewer["user_id"]
        )
        assigned.append({
            "label_hash": label_hash,
            "annotator_email": annotator_email,
            "assigned_reviewer": selected_reviewer["email"]
        })
    except Exception as e:
        skipped.append({
            "label_hash": label_hash,
            "annotator_email": annotator_email,
            "reason": str(e)
        })

#  Saving the logs
pd.DataFrame(assigned).to_csv("assigned_reviews.csv", index=False)
pd.DataFrame(skipped).to_csv("skipped_reviews.csv", index=False)

print(f"✅ {len(assigned)} reviews assigned.")
print(f"⚠️ {len(skipped)} tasks skipped. See skipped_reviews.csv for details.")
