# **Project Setup Instructions**
This guide will help you set up the environment and run the application.

Ensure you have the following installed:

     * Python 3.8+
     * uv package manager
       If not installed, follow the installation guide at [UV Package Manager Docs](https://github.com/astral-sh/uv).

**Setup Instructions**
**Create a Virtual Environment**
Create an isolated environment for the project. Run the following command:
1. Install [UV](https://github.com/astral-sh/uv)
2. Create virtual environment
    ```shell
    $ uv venv
    ```
3. Sync environment
    ```shell
    $ uv sync
    ```
4. Add dependencies
   ```shell
   $ uv add "[package]"
   ```
5. Remove dependencies
   ```shell
   $ uv remove "[package]"
   ```
6. Run application
   ```shell
   $ uv run app.py
   ```

