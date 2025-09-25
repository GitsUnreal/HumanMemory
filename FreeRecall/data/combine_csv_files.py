import csv
import os
from pathlib import Path

# Define the data directory
data_dir = Path("FreeRecall/data")

# Define the three categories and their corresponding files
categories = {
    "memorypattern": [
        "game_log_memorypatternRA.csv",
        "game_log_memorypatternSA.csv", 
        "game_log_memorypatternSO.csv"
    ],
    "normal": [
        "game_log_normalAS.csv",
        "game_log_normalRA.csv",
        "game_log_normalSA.csv",
        "game_log_normalSO.csv"
    ],
    "speed": [
        "game_log_speedAS.csv",
        "game_log_speedRA.csv",
        "game_log_speedSA.csv",
        "game_log_speedSO.csv"
    ]
}

# Function to combine CSV files for each category
def combine_csv_files(category, file_list):
    combined_rows = []
    header = None
    total_rows = 0
    
    for filename in file_list:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    file_header = next(reader)
                    
                    # Set header from first file or check consistency
                    if header is None:
                        header = file_header + ['source_file']  # Add source_file column
                    elif file_header != header[:-1]:  # Check if headers match (excluding source_file)
                        print(f"Warning: Header mismatch in {filename}")
                    
                    # Read all rows and add source file info
                    file_rows = 0
                    for row in reader:
                        row.append(filename)  # Add source file name
                        combined_rows.append(row)
                        file_rows += 1
                    
                    total_rows += file_rows
                    print(f"Added {filename} with {file_rows} rows")
                    
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        else:
            print(f"File not found: {filename}")
    
    if combined_rows:
        # Save the combined file
        output_file = data_dir / f"combined_{category}_data.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)  # Write header
            writer.writerows(combined_rows)  # Write all data rows
        
        print(f"Created {output_file} with {total_rows} total rows")
        return total_rows
    else:
        print(f"No data found for category: {category}")
        return 0

# Process each category
print("Combining CSV files by category...\n")

total_files_created = 0
for category, files in categories.items():
    print(f"Processing {category} category:")
    rows = combine_csv_files(category, files)
    if rows > 0:
        total_files_created += 1
    print(f"")

print(f"Successfully created {total_files_created} combined data files!")