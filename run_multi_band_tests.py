#!/usr/bin/env python3
"""
Test runner for multi-band functionality
Runs all tests related to the new multi-band features with detailed reporting.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_tests():
    """Run the multi-band tests with proper configuration."""
    print("🚀 Running Multi-Band Functionality Tests")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Test configuration
    test_files = [
        "tests/test_multi_band.py",
        "tests/conftest_multi_band.py"
    ]
    
    # Check if test files exist
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            return False
    
    # Run tests with different configurations
    test_configs = [
        {
            "name": "Basic Multi-Band Tests",
            "args": ["python", "-m", "pytest", "tests/test_multi_band.py", "-v", "--tb=short"]
        },
        {
            "name": "Multi-Band Tests with Coverage",
            "args": ["python", "-m", "pytest", "tests/test_multi_band.py", "--cov=app", "--cov-report=term-missing", "-v"]
        },
        {
            "name": "Multi-Band Tests (Fast)",
            "args": ["python", "-m", "pytest", "tests/test_multi_band.py", "-m", "not slow", "-v"]
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n🔍 Running: {config['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Run the test command
            result = subprocess.run(
                config["args"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            if result.returncode == 0:
                status = "✅ PASSED"
                # Extract test summary from output
                lines = result.stdout.split('\n')
                summary_line = [line for line in lines if 'passed' in line.lower() and 'failed' in line.lower()]
                summary = summary_line[0] if summary_line else "All tests passed"
            else:
                status = "❌ FAILED"
                summary = f"Exit code: {result.returncode}"
            
            results.append({
                "name": config["name"],
                "status": status,
                "duration": f"{duration:.2f}s",
                "summary": summary,
                "output": result.stdout,
                "errors": result.stderr
            })
            
            print(f"Status: {status}")
            print(f"Duration: {duration:.2f}s")
            print(f"Summary: {summary}")
            
            if result.stderr:
                print(f"Errors: {result.stderr[:200]}...")
            
        except subprocess.TimeoutExpired:
            status = "⏰ TIMEOUT"
            results.append({
                "name": config["name"],
                "status": status,
                "duration": ">300s",
                "summary": "Tests timed out after 5 minutes",
                "output": "",
                "errors": "Timeout"
            })
            print(f"Status: {status}")
            print("Tests timed out after 5 minutes")
            
        except Exception as e:
            status = "💥 ERROR"
            results.append({
                "name": config["name"],
                "status": status,
                "duration": "N/A",
                "summary": f"Error: {str(e)}",
                "output": "",
                "errors": str(e)
            })
            print(f"Status: {status}")
            print(f"Error: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if "PASSED" in r["status"])
    total = len(results)
    
    for result in results:
        print(f"{result['status']} | {result['name']} | {result['duration']}")
        print(f"    {result['summary']}")
        print()
    
    print(f"Overall: {passed}/{total} test configurations passed")
    
    if passed == total:
        print("🎉 All multi-band tests completed successfully!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

def check_prerequisites():
    """Check if all prerequisites are met for running tests."""
    print("🔍 Checking Prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 7):
        print(f"❌ Python 3.7+ required, found {python_version.major}.{python_version.minor}")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if required packages are installed
    required_packages = ['pytest', 'flask', 'sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check if app directory exists
    if not Path("app").exists():
        print("❌ App directory not found. Run this script from the project root.")
        return False
    print("✅ App directory found")
    
    # Check if database migration has been run
    if not Path("migrate_multi_band.py").exists():
        print("❌ Multi-band migration script not found.")
        return False
    print("✅ Multi-band migration script found")
    
    print("✅ All prerequisites met!")
    return True

def main():
    """Main function to run the test suite."""
    print("🎸 BandMate Multi-Band Test Suite")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return 1
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🎉 Multi-band functionality tests completed successfully!")
        print("The new multi-band features are working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
