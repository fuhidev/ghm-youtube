"""
Check environment variables required by the YouTube Tool.
"""

import os
import sys


def check_env():
    """Check if required environment variables are set"""
    print("Checking environment variables:")

    env_vars = {
        "DEEPSEEK_API_KEY": "DeepSeek API",
        "LEONARDO_API_KEY": "Leonardo.ai API",
    }

    all_set = True

    for var, description in env_vars.items():
        value = os.environ.get(var)
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✓ {var} is set ({description}: {masked})")
        else:
            print(f"✗ {var} is NOT set ({description})")
            all_set = False

    print("\nPath information:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    if not all_set:
        print("\nSome environment variables are missing. You can set them by:")
        print("\nOn Windows (Command Prompt):")
        print('    setx DEEPSEEK_API_KEY "your-key-here" /M')
        print('    setx LEONARDO_API_KEY "your-key-here" /M')
        print("\nOn Windows (PowerShell):")
        print(
            '    [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-key-here", "Machine")'
        )
        print(
            '    [Environment]::SetEnvironmentVariable("LEONARDO_API_KEY", "your-key-here", "Machine")'
        )
        print("\nOn Linux/macOS:")
        print('    export DEEPSEEK_API_KEY="your-key-here"')
        print('    export LEONARDO_API_KEY="your-key-here"')
        print("\nOr create a config.py file in the project root with these variables.")


if __name__ == "__main__":
    check_env()
