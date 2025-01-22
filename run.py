import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Get the absolute path to src/app.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "src", "app.py")
    
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())