from encord import EncordUserClient
import pandas as pd
import random

# Authenticate using your SSH private key
client = EncordUserClient.create_with_ssh_private_key(
    ssh_private_key_path="/Users/sonia.yizerwe/.ssh/id_ed25519"  # Replace with your actual path if different
)

# Load your specific Encord project
project = client.get_project("28a20d28-376e-474b-939a-97b55f36bf60")

# Get all label rows
label_rows = project.get_label_rows_v2()

# Get current user (optional auditing/logging)
current_user = client.get_user()

# Get all project users
project_users = project.get_project_users()
reviewers = [
    user for user in project_users
    if user.get("email")  # Optional: filter by role if needed
]

# Assign reviewers while avoiding self-review
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

# Save logs
pd.DataFrame(assigned).to_csv("assigned_reviews.csv", index=False)
pd.DataFrame(skipped).to_csv("skipped_reviews.csv", index=False)

print(f"✅ {len(assigned)} reviews assigned.")
print(f"⚠️ {len(skipped)} tasks skipped. See skipped_reviews.csv for details.")
