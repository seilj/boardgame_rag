import csv

def extract_third_column(file_path):
    """CSV 파일에서 3번째 열의 데이터를 리스트로 추출 (빈 칸은 제외)"""
    third_column_data = []
    
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            # 3번째 열이 존재하고, 값이 비어있지 않다면 추가
            if len(row) >= 3 and row[2].strip():
                third_column_data.append(row[2].strip())

    return third_column_data
