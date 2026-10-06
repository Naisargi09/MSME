import os
import sys
import subprocess
import venv

def run_cmd(args, env=None):
    """Helper to run system commands and stream output."""
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, args)

def main():
    print("==================================================")
    print("      MSME AI Operations Copilot Setup & Start    ")
    print("==================================================")
    
    # 1. Set up Virtual Environment
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv")
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

    # 2. Get Virtual Environment python and pip paths
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")

    # 3. Upgrade pip
    print("Upgrading pip...")
    try:
        run_cmd([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        print(f"Could not upgrade pip: {e}. Continuing anyway.")

    # 4. Install Dependencies
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    print(f"Installing dependencies from {req_file}...")
    run_cmd([venv_pip, "install", "-r", req_file])

    # 5. Create .env if not exists
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    env_example = os.path.join(os.path.dirname(__file__), ".env.example")
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print("Creating .env from .env.example...")
            with open(env_example, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            print(".env created. Please configure your GEMINI_API_KEY in it.")
        else:
            print("Warning: .env.example not found, could not create .env automatically.")
    else:
        print(".env already exists.")

    # 6. Generate MSME_sample_data.xlsx from MSME_sample_data.csv if not exists
    csv_file = os.path.join(os.path.dirname(__file__), "MSME_sample_data.csv")
    xlsx_file = os.path.join(os.path.dirname(__file__), "MSME_sample_data.xlsx")
    if os.path.exists(csv_file) and not os.path.exists(xlsx_file):
        print("Generating MSME_sample_data.xlsx from CSV using pandas...")
        gen_script = f"""
import pandas as pd
df = pd.read_csv(r"{csv_file}")
df.to_excel(r"{xlsx_file}", index=False)
print("Successfully generated MSME_sample_data.xlsx.")
"""
        try:
            subprocess.run([venv_python, "-c", gen_script], check=True)
        except Exception as e:
            print(f"Could not generate Excel file: {e}")

    # 7. Start the Flask Application
    app_py = os.path.join(os.path.dirname(__file__), "backend", "app.py")
    print("\nStarting the MSME AI Operations Copilot server...")
    print("Press Ctrl+C to stop.\n")
    try:
        run_cmd([venv_python, app_py])
    except KeyboardInterrupt:
        print("\nStopping server.")

if __name__ == "__main__":
    main()
