#!/usr/bin/env python3
"""
Repository Analysis Script for GGnet Cleanup Phase 0

Analyzes repository structure, finds unused files, dead code, and duplicates.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import subprocess


def get_git_info(file_path: str) -> Dict:
    """Get git information for a file"""
    try:
        # Last commit date
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=iso', '--', file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        last_commit = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        # File size
        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return {
            "path": file_path,
            "size": size,
            "last_commit": last_commit,
            "extension": Path(file_path).suffix
        }
    except Exception as e:
        return {
            "path": file_path,
            "size": 0,
            "last_commit": "Error",
            "extension": Path(file_path).suffix
        }


def scan_directory(base_path: str, exclude_patterns: List[str]) -> List[Dict]:
    """Scan directory and collect file information"""
    files = []
    
    for root, dirs, filenames in os.walk(base_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in os.path.join(root, d) for pattern in exclude_patterns)]
        
        for filename in filenames:
            filepath = os.path.join(root, filename)
            
            # Skip excluded patterns
            if any(pattern in filepath for pattern in exclude_patterns):
                continue
            
            try:
                info = get_git_info(filepath)
                files.append(info)
            except Exception:
                pass
    
    return files


def analyze_python_imports(base_path: str) -> Dict[str, Set[str]]:
    """Analyze Python imports to find unused modules"""
    imports = {}
    
    for root, dirs, filenames in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git']]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Find imports
                    file_imports = set()
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            file_imports.add(line)
                    
                    if file_imports:
                        imports[filepath] = file_imports
                        
                except Exception:
                    pass
    
    return imports


def find_duplicate_files(files: List[Dict]) -> List[List[Dict]]:
    """Find potential duplicate files by size"""
    size_map = {}
    
    for file_info in files:
        size = file_info['size']
        if size > 0:  # Ignore empty files
            if size not in size_map:
                size_map[size] = []
            size_map[size].append(file_info)
    
    # Find duplicates (same size)
    duplicates = []
    for size, file_list in size_map.items():
        if len(file_list) > 1:
            duplicates.append(file_list)
    
    return duplicates


def categorize_files(files: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize files by type"""
    categories = {
        'python': [],
        'javascript': [],
        'typescript': [],
        'config': [],
        'docs': [],
        'templates': [],
        'cache': [],
        'other': []
    }
    
    for file_info in files:
        ext = file_info['extension'].lower()
        path = file_info['path']
        
        if ext == '.py':
            categories['python'].append(file_info)
        elif ext in ['.js', '.jsx']:
            categories['javascript'].append(file_info)
        elif ext in ['.ts', '.tsx']:
            categories['typescript'].append(file_info)
        elif ext in ['.json', '.yml', '.yaml', '.toml', '.ini', '.conf']:
            categories['config'].append(file_info)
        elif ext in ['.md', '.txt', '.rst']:
            categories['docs'].append(file_info)
        elif ext in ['.template', '.example']:
            categories['templates'].append(file_info)
        elif 'cache' in path.lower():
            categories['cache'].append(file_info)
        else:
            categories['other'].append(file_info)
    
    return categories


def identify_legacy_files(files: List[Dict]) -> Dict[str, List[str]]:
    """Identify potentially legacy/unused files"""
    legacy = {
        'old_scripts': [],
        'backup_files': [],
        'test_files': [],
        'cache_files': [],
        'duplicate_configs': []
    }
    
    for file_info in files:
        path = file_info['path']
        filename = Path(path).name.lower()
        
        # Old/backup files
        if any(keyword in filename for keyword in ['old', 'backup', 'bak', 'tmp', 'temp', '_old', '.bak']):
            legacy['backup_files'].append(path)
        
        # Test/debug files
        if any(keyword in filename for keyword in ['test_', 'debug_', 'check_', 'simple_']):
            if 'tests/' not in path:  # Exclude actual test directory
                legacy['test_files'].append(path)
        
        # Cache files
        if any(keyword in path for keyword in ['cache/', '.cache', '__pycache__']):
            legacy['cache_files'].append(path)
        
        # Duplicate configs
        if filename.endswith('.example') or filename.endswith('.template'):
            base_name = filename.replace('.example', '').replace('.template', '')
            base_path = str(Path(path).parent / base_name)
            if os.path.exists(base_path):
                legacy['duplicate_configs'].append(f"{path} (actual: {base_path})")
    
    return legacy


def main():
    print("Analyzing GGnet repository...")
    print("=" * 60)
    
    base_path = "."
    exclude_patterns = [
        'node_modules',
        'venv',
        '__pycache__',
        '.git',
        'dist',
        'build',
        '.pytest_cache',
        '.mypy_cache'
    ]
    
    # Scan files
    print("Scanning files...")
    files = scan_directory(base_path, exclude_patterns)
    print(f"Found {len(files)} files")
    
    # Categorize
    print("\nCategorizing files...")
    categories = categorize_files(files)
    for cat, file_list in categories.items():
        print(f"  {cat}: {len(file_list)} files")
    
    # Find duplicates
    print("\nFinding potential duplicates...")
    duplicates = find_duplicate_files(files)
    print(f"Found {len(duplicates)} groups of potential duplicates")
    
    # Identify legacy
    print("\nIdentifying legacy files...")
    legacy = identify_legacy_files(files)
    for cat, file_list in legacy.items():
        print(f"  {cat}: {len(file_list)} files")
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(files),
        "categories": {k: len(v) for k, v in categories.items()},
        "legacy_files": {k: len(v) for k, v in legacy.items()},
        "duplicate_groups": len(duplicates),
        "files": files,
        "legacy_details": legacy
    }
    
    # Save detailed inventory
    with open('repo_inventory_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Detailed report saved to: repo_inventory_detailed.json")
    print("=" * 60)
    
    return report


if __name__ == "__main__":
    main()

