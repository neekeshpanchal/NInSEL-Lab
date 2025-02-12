import pandas as pd

def convert_dlc_to_diplomat(dlc_csv_path, output_csv_path):
    # Load the DLC CSV file
    dlc_df = pd.read_csv(dlc_csv_path, header=None)
    
    # Remove first column (frame numbers) and first row (scorer row)
    dlc_df = dlc_df.iloc[1:, :].reset_index(drop=True)  # Drop only the first row initially
    
    # Extract the required header structure
    individuals = dlc_df.iloc[0, 1:].values  # Skip the first column
    bodyparts = dlc_df.iloc[1, 1:].values  # Skip the first column
    coordinates = dlc_df.iloc[2, 1:].values  # Skip the first column
    
    # Construct the new header
    header = pd.DataFrame({
        "body": individuals,
        "bodypart": bodyparts,
        "coords": coordinates
    })
    
    # Retain pose data from row 4 onward (after the headers) and drop the first column
    pose_data = dlc_df.iloc[3:, 1:].reset_index(drop=True)
    
    # Ensure pose data is shifted left to align with the headers
    pose_data.columns = range(pose_data.shape[1])  # Reset column indexing
    
    # Concatenate headers with data
    result_df = pd.concat([header.T.reset_index(drop=True), pose_data], ignore_index=True)
    
    # Save to CSV in the corrected format
    result_df.to_csv(output_csv_path, index=False, header=False)
    
    print(f"Converted file saved to {output_csv_path}")

# Example usage
dlc_csv_path = "bikingDLC_resnet50_PPC1 SocialNov12shuffle1_50000_el.csv"
output_csv_path = "corrected_diplomat.csv"
convert_dlc_to_diplomat(dlc_csv_path, output_csv_path)