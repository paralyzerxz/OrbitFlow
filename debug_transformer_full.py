import traceback
import sys
import os

print("--- DEBUG TRANSFORMER ---")
try:
    import transformer
    print("Transformer module imported successfully.")
    
    # Check if input file exists
    if os.path.exists(transformer.INPUT_FILE):
        print(f"Input file found: {transformer.INPUT_FILE}")
    else:
        print(f"ERROR: Input file NOT found: {transformer.INPUT_FILE}")
        sys.exit(1)
        
    print("Starting transformation...")
    transformer.transform()
    print("Transformation finished.")
    
except Exception as e:
    print("\n!!! CRITICAL ERROR DURING TRANSFORMATION !!!")
    traceback.print_exc()
    sys.exit(1)
