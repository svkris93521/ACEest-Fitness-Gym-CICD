
import subprocess
import asyncio
import pytest


def start_ace():
    # Clean up any existing containers and images
    subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)

def stop_ace():
    subprocess.run(["docker-compose", "down"], check=True)
    subprocess.run(["docker-compose", "down", "--rmi", "all"], check=True)

def test_ace():
    subprocess.run([
        "python3", "-m", "pytest", 
        "hms_tests.py", 
        "-v", 
        "-o", "asyncio_mode=auto"
    ], check=True)


#pass STOP or START as command line argument to stop or start the services 
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "STOP":
            stop_ace()
        elif sys.argv[1] == "START":
            start_ace()
        elif sys.argv[1] == "TEST":
            test_ace()
        else:
            print("Invalid argument. Use STOP, START, or TEST.")
    else:        print("No argument provided. Use STOP, START, or TEST.")
