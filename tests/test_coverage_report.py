"""
Test Coverage Report

Generates a comprehensive report of test coverage for the application.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

def get_test_files() -> List[str]:
    """Get all test files in the tests directory."""
    tests_dir = Path("tests")
    test_files = []
    
    if tests_dir.exists():
        for file in tests_dir.glob("test_*.py"):
            test_files.append(str(file))
    
    return test_files

def get_source_files() -> List[str]:
    """Get all source files in the src directory."""
    src_dir = Path("src")
    source_files = []
    
    if src_dir.exists():
        for file in src_dir.glob("*.py"):
            source_files.append(str(file))
    
    return source_files

def count_test_methods(test_file: str) -> int:
    """Count the number of test methods in a test file."""
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Count lines that start with "def test_"
            test_methods = [line for line in content.split('\n') 
                          if line.strip().startswith('def test_')]
            return len(test_methods)
    except Exception:
        return 0

def analyze_test_coverage() -> Dict[str, any]:
    """Analyze test coverage and return a comprehensive report."""
    test_files = get_test_files()
    source_files = get_source_files()
    
    # Count test methods in each file
    test_methods_by_file = {}
    total_test_methods = 0
    
    for test_file in test_files:
        method_count = count_test_methods(test_file)
        test_methods_by_file[test_file] = method_count
        total_test_methods += method_count
    
    # Analyze source files
    source_analysis = {}
    total_source_lines = 0
    
    for source_file in source_files:
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                source_analysis[source_file] = {
                    'lines': len(lines),
                    'code_lines': len([line for line in lines if line.strip() and not line.strip().startswith('#')])
                }
                total_source_lines += len(lines)
        except Exception:
            source_analysis[source_file] = {'lines': 0, 'code_lines': 0}
    
    return {
        'test_files': test_files,
        'source_files': source_files,
        'test_methods_by_file': test_methods_by_file,
        'total_test_methods': total_test_methods,
        'source_analysis': source_analysis,
        'total_source_lines': total_source_lines
    }

def generate_coverage_report() -> str:
    """Generate a comprehensive coverage report."""
    analysis = analyze_test_coverage()
    
    report = []
    report.append("=" * 80)
    report.append("TEST COVERAGE REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Test Files Summary
    report.append("📁 TEST FILES SUMMARY")
    report.append("-" * 40)
    report.append(f"Total test files: {len(analysis['test_files'])}")
    report.append(f"Total test methods: {analysis['total_test_methods']}")
    report.append("")
    
    for test_file, method_count in analysis['test_methods_by_file'].items():
        report.append(f"  {test_file}: {method_count} test methods")
    report.append("")
    
    # Source Files Summary
    report.append("📁 SOURCE FILES SUMMARY")
    report.append("-" * 40)
    report.append(f"Total source files: {len(analysis['source_files'])}")
    report.append(f"Total source lines: {analysis['total_source_lines']}")
    report.append("")
    
    for source_file, stats in analysis['source_analysis'].items():
        report.append(f"  {source_file}: {stats['lines']} lines ({stats['code_lines']} code)")
    report.append("")
    
    # Coverage Categories
    report.append("📊 COVERAGE CATEGORIES")
    report.append("-" * 40)
    
    # Core functionality tests
    core_tests = ['test_automator.py', 'test_thread_safety.py', 'test_ui_session.py']
    core_test_methods = sum(analysis['test_methods_by_file'].get(f"tests/{test}", 0) 
                           for test in core_tests)
    report.append(f"Core functionality tests: {core_test_methods} methods")
    
    # Service tests
    service_tests = ['test_coordinate_service.py', 'test_countdown_service.py', 
                    'test_file_service.py', 'test_flexible_parser.py']
    service_test_methods = sum(analysis['test_methods_by_file'].get(f"tests/{test}", 0) 
                              for test in service_tests)
    report.append(f"Service tests: {service_test_methods} methods")
    
    # Thread safety tests
    thread_safety_tests = ['test_thread_safety.py']
    thread_safety_methods = sum(analysis['test_methods_by_file'].get(f"tests/{test}", 0) 
                               for test in thread_safety_tests)
    report.append(f"Thread safety tests: {thread_safety_methods} methods")
    
    # UI session tests
    ui_session_tests = ['test_ui_session.py']
    ui_session_methods = sum(analysis['test_methods_by_file'].get(f"tests/{test}", 0) 
                            for test in ui_session_tests)
    report.append(f"UI session tests: {ui_session_methods} methods")
    report.append("")
    
    # Test Coverage Assessment
    report.append("📈 TEST COVERAGE ASSESSMENT")
    report.append("-" * 40)
    
    total_tests = analysis['total_test_methods']
    total_source_files = len(analysis['source_files'])
    
    if total_source_files > 0:
        tests_per_file = total_tests / total_source_files
        report.append(f"Average tests per source file: {tests_per_file:.1f}")
    
    # Coverage recommendations
    report.append("")
    report.append("🎯 COVERAGE RECOMMENDATIONS")
    report.append("-" * 40)
    
    if core_test_methods < 20:
        report.append("⚠️  Core functionality tests need more coverage")
    else:
        report.append("✅ Core functionality tests have good coverage")
    
    if thread_safety_methods < 10:
        report.append("⚠️  Thread safety tests need more coverage")
    else:
        report.append("✅ Thread safety tests have good coverage")
    
    if ui_session_methods < 10:
        report.append("⚠️  UI session tests need more coverage")
    else:
        report.append("✅ UI session tests have good coverage")
    
    if service_test_methods < 50:
        report.append("⚠️  Service tests need more coverage")
    else:
        report.append("✅ Service tests have good coverage")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Main function to generate and display the coverage report."""
    try:
        report = generate_coverage_report()
        print(report)
        
        # Save report to file
        with open("test_coverage_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        print("\n📄 Coverage report saved to: test_coverage_report.txt")
        
    except Exception as e:
        print(f"Error generating coverage report: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
