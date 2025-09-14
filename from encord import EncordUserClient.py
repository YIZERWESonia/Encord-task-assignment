from encord import EncordUserClient
import pandas as pd

# Authenticate using your Encord API key JSON file
client = EncordUserClient.create_with_ssh_private_key(
    json_credentials_path="your_api_key.json"
)

#  Replace with your actual project hash
project = client.get_project("your_project_hash_here")

#  Fetch label rows
label_rows = project.get_label_rows_v2()

#  Get current reviewer ID
current_user = client.get_user()
reviewer_id = current_user["user_id"]

#  Collect label row data
rows = []
for label_hash, data in label_rows.items():
    annotator = data.get("dataset_row", {}).get("created_by", "")
    reviewer = data.get("last_edited_by", "")
    status = data.get("label_status", "")
    
    if status == "LABELLED" and annotator != reviewer_id:
        rows.append({
            "label_hash": label_hash,
            "annotator": annotator,
            "reviewer": reviewer,
            "status": status
        })

#  Save results to CSV
df = pd.DataFrame(rows)
df.to_csv("review_queue_not_self_annotated.csv", index=False)
print("Filtered review queue saved as CSV.")
