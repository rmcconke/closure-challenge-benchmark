from closure_challenge import score_from_csv, evaluate_from_csv_by_case
from tabulate import tabulate
import os

# Collect all scores
competitors = {}

# Montoya
competitors['Montoya, Oulghelou, and Cinnella'] = {
    'total': score_from_csv(os.path.join('submissions', 'montoya')),
    'cases': evaluate_from_csv_by_case(os.path.join('submissions', 'montoya')),
    'link': 'https://doi.org/10.1007/s10494-025-00661-8'
}

# Reissmann
reissmann_paths = {
    "alpha_15_13929_4048": "submissions/reissmann/alpha_15_13929_4048/predictions.csv",
    "alpha_15_13929_2024": "submissions/reissmann/alpha_15_13929_2024/predictions.csv",
    "alpha_05_4071_4048": "submissions/reissmann/alpha_05_4071_4048/predictions.csv",
    "alpha_05_4071_2024": "submissions/reissmann/alpha_05_4071_2024/predictions.csv",
    "AR_1_Ret_360": "submissions/reissmann/AR_1_Ret_360/predictions.csv",
    "AR_3_Ret_360": "submissions/reissmann/AR_3_Ret_360/predictions.csv",
    "AR_14_Ret_180": "submissions/reissmann/AR_14_Ret_180/predictions.csv",
    "NASA_2DWMH": "submissions/reissmann/NASA_2DWMH/predictions.csv"
}
competitors['Reissmann, Fang, and Sandberg'] = {
    'total': score_from_csv(reissmann_paths),
    'cases': evaluate_from_csv_by_case(reissmann_paths),
    'link': 'https://github.com/rmcconke/closure-challenge-benchmark/blob/main/submissions/reissmann/score_eval.ipynb'
}

# Wu
competitors['Wu and Zhang'] = {
    'total': score_from_csv(os.path.join('submissions', 'wu')),
    'cases': evaluate_from_csv_by_case(os.path.join('submissions', 'wu')),
    'link': 'https://github.com/rmcconke/closure-challenge-benchmark/blob/main/submissions/wu/description_document.pdf'
}

competitors['Liu, Wang, Zhao, and Xiao'] = {
    'total': score_from_csv(os.path.join('submissions', 'wang')),
    'cases': evaluate_from_csv_by_case(os.path.join('submissions', 'wang')),
    'link': 'https://arxiv.org/abs/2509.17189'
}

# Sort by total score ascending (lower is better)
sorted_competitors = sorted(competitors.items(), key=lambda x: x[1]['total'], reverse=False)

# Get case names from first competitor
case_names = list(sorted_competitors[0][1]['cases'].keys())

# Build table data
table_data = []
for rank, (name, data) in enumerate(sorted_competitors, 1):
    row = [rank, f"[{name}]({data['link']})", f"{data['total']:.4f}"]
    row += [f"{float(data['cases'][case]):.4f}" for case in case_names]
    table_data.append(row)

# Print markdown table
headers = ['Rank', 'Authors', 'Overall'] + case_names
print(tabulate(table_data, headers=headers, tablefmt='github'))