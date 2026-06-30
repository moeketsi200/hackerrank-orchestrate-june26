import os
import sys

# __file__ is code/evaluation/main.py
code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, code_dir)

import main as main_module
process_claims = main_module.process_claims
import pandas as pd
import time

def evaluate():
    input_file = "dataset/sample_claims.csv"
    output_file = "evaluation_output.csv"
    
    print("Running evaluation on sample claims...")
    
    start_time = time.time()
    process_claims(input_file, output_file)
    end_time = time.time()
    
    # Compare output_file with input_file
    expected_df = pd.read_csv(input_file)
    actual_df = pd.read_csv(output_file)
    
    metrics = {
        "claim_status": 0,
        "issue_type": 0,
        "object_part": 0,
        "evidence_standard_met": 0
    }
    
    total = len(expected_df)
    
    print("\n--- Model Output vs Expected ---")
    for i in range(total):
        if str(expected_df.iloc[i]['claim_status']).lower() == str(actual_df.iloc[i]['claim_status']).lower():
            metrics['claim_status'] += 1
        if str(expected_df.iloc[i]['issue_type']).lower() == str(actual_df.iloc[i]['issue_type']).lower():
            metrics['issue_type'] += 1
        if str(expected_df.iloc[i]['object_part']).lower() == str(actual_df.iloc[i]['object_part']).lower():
            metrics['object_part'] += 1
        if str(expected_df.iloc[i]['evidence_standard_met']).lower() == str(actual_df.iloc[i]['evidence_standard_met']).lower():
            metrics['evidence_standard_met'] += 1
            
    print("\n--- Evaluation Results ---")
    print(f"Total Claims Processed: {total}")
    print(f"Total Time: {end_time - start_time:.2f} seconds")
    print(f"Average Time per Claim: {(end_time - start_time) / total:.2f} seconds")
    print(f"Claim Status Accuracy: {metrics['claim_status']}/{total} ({(metrics['claim_status']/total)*100:.1f}%)")
    print(f"Issue Type Accuracy: {metrics['issue_type']}/{total} ({(metrics['issue_type']/total)*100:.1f}%)")
    print(f"Object Part Accuracy: {metrics['object_part']}/{total} ({(metrics['object_part']/total)*100:.1f}%)")
    print(f"Evidence Standard Met Accuracy: {metrics['evidence_standard_met']}/{total} ({(metrics['evidence_standard_met']/total)*100:.1f}%)")
    print("\nEvaluation output saved to 'evaluation_output.csv'")

if __name__ == "__main__":
    evaluate()
