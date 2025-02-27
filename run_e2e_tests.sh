#!/bin/bash

# Initialize variables
target=""
target_url=""
is_headless=false # Default is false (not headless)
is_load_test=false # Default is false (not load test)
requirements_file="e2e/requirements.txt"
pytest_config_file="e2e/pytest.ini"

# Function to parse arguments for flexibility
parse_args() {
    for arg in "$@"
    do
        case $arg in
            target=*)
                target="${arg#*=}"
                shift # Remove once we have processed it
                ;;
            target_url=*)
                target_url="${arg#*=}"
                shift # Remove once we have processed it
                ;;
            --is-headless)
                is_headless="true"
                shift # Remove once we have processed it
                ;;
            --is-load-test)
                is_load_test="true"
                shift # Remove once we have processed it
                ;;
            *)
                # Assume it's the target_url if target is already set
                if [ -n "$target" ] && [ -z "$target_url" ]; then
                    target_url="$arg"
                elif [ -z "$target" ]; then
                    target="$arg"
                fi
                shift
                ;;
        esac
    done
}

# Load environment variables for tests requiring credentials
# This includes variables like:
# - TEST_USER_EMAIL
# - TEST_USER_PASSWORD
# - TEST_REPR_INVITE_CASE_ID
if [ -f .e2e.env ]; then
    export $(cat .e2e.env | xargs)
elif [ -f e2e/.e2e.env ]; then
    export $(cat e2e/.e2e.env | xargs)
else
    echo "Warning: .e2e.env file not found in current directory or e2e/. Some tests may fail."
    exit 1
fi

# Parse the input arguments
parse_args "$@"

# Activate python virtual environment
source .venv/bin/activate

# Install python dependencies from the chosen requirements file
pip install -r $requirements_file

if [ -z "$target_url" ]; then
    echo "Error: No target URL specified."
    exit 1
fi


# Normal end-to-end testing with Playwright and pytest
PWDEBUG=0 BASE_FRONTEND_TESTING_URL="$target_url" TEST_HEADLESS="$is_headless" pytest -c $pytest_config_file "e2e/$target"

# Deactivate python virtual environment
deactivate
