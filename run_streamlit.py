import sys
import os
from pathlib import Path

# Add the project root to the Python path
root_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_path))

# Run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", str(root_path / "app" / "web" / "app.py"), "--server.port=8501"]
    sys.exit(stcli.main())

