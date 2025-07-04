import pandas as pd
from collections import defaultdict
import os

# 파일 경로
excel_path = "/mnt/c/Users/jaeho.p/Desktop/webc-prod_sg_findings_25_06_02.xlsx"
tf_path = "/mnt/c/Users/jaeho.p/Desktop/SRE/webconnect-infra-terraform/wc025/prod/security-group.tf"
output_path = "/mnt/c/Users/jaeho.p/Desktop/security-group_annotated.tf"

# Excel 파일 로드
df = pd.read_excel(excel_path)

# SG 이름 기준으로 주석 내용 정리
findings_by_sg = defaultdict(list)
for _, row in df.iterrows():
    sg_name = str(row['Security Group Name']).strip()
    finding = str(row['Findings']).strip()
    direction = str(row['Direction']).strip()
    protocol = str(row['Protocol']).strip()
    port = str(row['Port Range']).strip()
    src = str(row['Src Parsed']).strip()
    dst = str(row['Des Parsed']).strip()
    desc = str(row['Rules Src/Dst Description']).strip()

    comment = f"- [{direction}] {finding}"
    if protocol and port and port != "-":
        comment += f" (Protocol: {protocol}, Port: {port})"
    if src and src != "-":
        comment += f", Source: {src}"
    if dst and dst != "-":
        comment += f", Destination: {dst}"
    if desc and desc != "-":
        comment += f" — {desc}"

    findings_by_sg[sg_name].append(comment)

# Terraform 파일 읽기
with open(tf_path, "r") as f:
    tf_lines = f.readlines()

# SG 이름에서 핵심 식별자 추출 함수
def extract_identifier(sg_name):
    # 예: sgs-wc025-prod-nginx-internal-alb-ue1 → nginx, alb 등으로 나눠서 탐지
    parts = sg_name.replace("sgs-", "").replace("eks-cluster-sg-", "").split("-")
    return [p for p in parts if len(p) > 2]

# TF에 주석 삽입
annotated_tf_lines = []
for line in tf_lines:
    matched = False
    for sg_name, comments in findings_by_sg.items():
        identifiers = extract_identifier(sg_name)
        if any(idf in line for idf in identifiers):
            annotated_tf_lines.append("\n".join([f"# {c}" for c in comments]) + "\n")
            matched = True
            break
    annotated_tf_lines.append(line)

# 결과 저장
try:
    with open(output_path, "w") as f:
        f.writelines(annotated_tf_lines)
    print("✅ 주석 추가 완료:", output_path)
except Exception as e:
    print("❌ 파일 쓰기 실패:", e)
