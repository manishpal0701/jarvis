import subprocess
import os
import time

def test_command_line():
    # Create a simple JSX script that writes a file to verify execution
    test_log = os.path.abspath("scratch/jsx_run_success.txt")
    if os.path.exists(test_log):
        os.remove(test_log)
        
    jsx_content = f"""
    var f = new File("{test_log.replace('\\', '\\\\')}");
    f.open("w");
    f.write("Success at " + new Date().toString());
    f.close();
    """
    
    jsx_path = os.path.abspath("scratch/test_cmd.jsx")
    with open(jsx_path, "w") as f:
        f.write(jsx_content)
        
    print(f"JSX script written to {jsx_path}")
    
    premiere_path = r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
    
    # Try running Premiere Pro with the script as a direct argument
    cmd = [premiere_path, jsx_path]
    print(f"Running command: {' '.join(cmd)}")
    
    # Start the process
    proc = subprocess.Popen(cmd)
    
    print("Waiting 30 seconds to see if the file is created...")
    for i in range(30):
        time.sleep(1)
        if os.path.exists(test_log):
            print("Success! The JSX script ran and created the log file.")
            with open(test_log, "r") as f:
                print(f"File content: {f.read()}")
            break
    else:
        print("File was not created within 10 seconds.")
        
    # Terminate the process if it's still running (since it launches Premiere Pro)
    print("Terminating Premiere Pro process...")
    proc.terminate()

if __name__ == "__main__":
    test_command_line()
