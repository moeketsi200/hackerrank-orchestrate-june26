import os
import pandas as pd
from dotenv import load_dotenv
import time

from model_client import init_client, analyze_claim_with_gemini
from prompting import build_user_prompt

def process_claims(input_file: str, output_file: str):
    load_dotenv()
    client = init_client()

    claims_df = pd.read_csv(input_file)
    history_df = pd.read_csv("dataset/user_history.csv")
    requirements_df = pd.read_csv("dataset/evidence_requirements.csv")

    results = []
    
    for idx, row in claims_df.iterrows():
        user_id = row['user_id']
        original_image_paths = row['image_paths'].split(';')
        actual_image_paths = [os.path.join("dataset", p) for p in original_image_paths]
        user_claim = row['user_claim']
        claim_object = row['claim_object']

        # Get history
        history_row = history_df[history_df['user_id'] == user_id]
        if not history_row.empty:
            history_summary = history_row.iloc[0]['history_summary']
            history_flags = history_row.iloc[0]['history_flags']
        else:
            history_summary = "No prior history"
            history_flags = "none"

        # Get evidence requirements for object and 'all'
        reqs = requirements_df[requirements_df['claim_object'].isin([claim_object, 'all'])]
        req_texts = []
        for _, req_row in reqs.iterrows():
            req_texts.append(f"- {req_row['applies_to']}: {req_row['minimum_image_evidence']}")
        evidence_requirements_text = "\n".join(req_texts)

        # Extract image IDs
        image_ids = [os.path.splitext(os.path.basename(p))[0] for p in original_image_paths]

        prompt = build_user_prompt(
            claim_object=claim_object,
            claim_conversation=user_claim,
            evidence_requirements=evidence_requirements_text,
            user_history_summary=history_summary,
            user_history_flags=history_flags,
            image_ids=image_ids
        )

        print(f"Processing claim {idx+1}/{len(claims_df)} for user {user_id}")
        
        # Add a delay to avoid rate limits (15 RPM for free tier Flash)
        time.sleep(4)
        
        assessment = analyze_claim_with_gemini(client, prompt, actual_image_paths)

        # Build row
        row_data = {
            "user_id": user_id,
            "image_paths": row['image_paths'],
            "user_claim": user_claim,
            "claim_object": claim_object,
            "evidence_standard_met": str(assessment.evidence_standard_met).lower(),
            "evidence_standard_met_reason": assessment.evidence_standard_met_reason,
            "risk_flags": assessment.risk_flags,
            "issue_type": assessment.issue_type,
            "object_part": assessment.object_part,
            "claim_status": assessment.claim_status,
            "claim_status_justification": assessment.claim_status_justification,
            "supporting_image_ids": assessment.supporting_image_ids,
            "valid_image": str(assessment.valid_image).lower(),
            "severity": assessment.severity
        }
        results.append(row_data)
        
        # Save progressively to output_file
        out_df = pd.DataFrame(results)
        columns_order = [
            "user_id", "image_paths", "user_claim", "claim_object", 
            "evidence_standard_met", "evidence_standard_met_reason", 
            "risk_flags", "issue_type", "object_part", "claim_status", 
            "claim_status_justification", "supporting_image_ids", 
            "valid_image", "severity"
        ]
        for col in columns_order:
            if col not in out_df.columns:
                out_df[col] = "unknown"
        out_df = out_df[columns_order]
        out_df.to_csv(output_file, index=False)

    print(f"Finished processing. Output written to {output_file}")

if __name__ == "__main__":
    process_claims("dataset/claims.csv", "output.csv")
