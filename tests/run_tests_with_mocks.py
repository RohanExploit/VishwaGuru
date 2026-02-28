
import sys
from unittest.mock import MagicMock

# Mock all heavy/missing dependencies
mock_modules = [
    'google',
    'google.generativeai',
    'google.api_core',
    'google.auth',
    'google.cloud',
    'ultralytics',
    'torch',
    'transformers',
    'telegram',
    'telegram.ext',
    'speech_recognition',
    'a2wsgi',
    'firebase_functions',
    'googletrans',
    'langdetect',
    'pywebpush'
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()

# Specifically mock torch.Tensor to avoid issubclass issues if needed
class MockTensor:
    pass

sys.modules['torch'].Tensor = MockTensor

import pytest
import os

if __name__ == "__main__":
    os.environ["AI_SERVICE_TYPE"] = "mock"
    os.environ["ENVIRONMENT"] = "testing"
    # Run pytest on specific test files
    sys.exit(pytest.main(["tests/test_blockchain.py", "tests/test_cache_update.py", "tests/test_user_issues.py"]))
