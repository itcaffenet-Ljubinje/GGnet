#!/usr/bin/env python3
"""
PDB Information Extractor for .NET PDB Files

This script extracts information from .NET Program Database (PDB) files including:
- Function/method names
- Class structures and namespaces
- Source file paths
- Type information
- Line mappings
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import struct
import re
import shutil

# Try to import optional dependencies
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PDBExtractor:
    """Extracts information from .NET PDB files"""
    
    def __init__(self, pdb_path: str, output_path: Optional[str] = None):
        self.pdb_path = Path(pdb_path)
        self.output_path = Path(output_path) if output_path else self.pdb_path.with_suffix('.txt')
        self.console = Console() if RICH_AVAILABLE else None
        
        if not self.pdb_path.exists():
            raise FileNotFoundError(f"PDB file not found: {self.pdb_path}")
        
        # Storage for extracted information
        self.namespaces: Set[str] = set()
        self.classes: List[Dict] = []
        self.methods: List[Dict] = []
        self.source_files: List[str] = []
        self.types: List[Dict] = []
        self.line_mappings: List[Dict] = []
        self.metadata: Dict = {}
        
    def find_windows_sdk_tools(self) -> Dict[str, Optional[Path]]:
        """Find Windows SDK tools for PDB analysis"""
        tools = {
            'cvdump': None,
            'pdb2xml': None,
            'dotnet': None
        }
        
        # Common Windows SDK paths
        program_files = Path(os.environ.get('ProgramFiles', 'C:\\Program Files'))
        program_files_x86 = Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'))
        
        # Search for cvdump.exe
        possible_paths = [
            program_files / 'Windows Kits' / '10' / 'bin' / 'x64' / 'cvdump.exe',
            program_files_x86 / 'Windows Kits' / '10' / 'bin' / 'x64' / 'cvdump.exe',
            program_files / 'Windows Kits' / '10' / 'bin' / '10.0.22621.0' / 'x64' / 'cvdump.exe',
        ]
        
        for path in possible_paths:
            if path.exists():
                tools['cvdump'] = path
                break
        
        # Search for pdb2xml.exe (part of .NET SDK)
        dotnet_paths = [
            program_files / 'dotnet' / 'pdb2xml.exe',
            Path(os.environ.get('ProgramFiles', '')) / 'dotnet' / 'pdb2xml.exe',
        ]
        
        # Also check if dotnet CLI is available
        dotnet_cli = shutil.which('dotnet')
        if dotnet_cli:
            tools['dotnet'] = Path(dotnet_cli)
            # pdb2xml might be in the same directory
            dotnet_dir = Path(dotnet_cli).parent
            pdb2xml_path = dotnet_dir / 'pdb2xml.exe'
            if pdb2xml_path.exists():
                tools['pdb2xml'] = pdb2xml_path
        
        return tools
    
    def extract_with_cvdump(self) -> Optional[str]:
        """Extract information using cvdump.exe"""
        tools = self.find_windows_sdk_tools()
        
        if not tools['cvdump']:
            return None
        
        try:
            result = subprocess.run(
                [str(tools['cvdump']), str(self.pdb_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"cvdump error: {result.stderr}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error running cvdump: {e}", file=sys.stderr)
            return None
    
    def extract_with_pdb2xml(self) -> Optional[str]:
        """Extract information using pdb2xml.exe"""
        tools = self.find_windows_sdk_tools()
        
        if not tools['pdb2xml']:
            return None
        
        try:
            result = subprocess.run(
                [str(tools['pdb2xml']), str(self.pdb_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"pdb2xml error: {result.stderr}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error running pdb2xml: {e}", file=sys.stderr)
            return None
    
    def parse_binary_pdb(self):
        """Attempt to parse PDB file directly from binary format"""
        try:
            with open(self.pdb_path, 'rb') as f:
                # Read PDB header
                # .NET PDB files have a specific structure
                # This is a simplified parser - full parsing is complex
                
                data = f.read()
                
                # Check for PDB signature
                if data[:4] == b'BSJB':  # Portable PDB signature
                    self.metadata['format'] = 'Portable PDB'
                    self._parse_portable_pdb(data)
                elif data[:4] == b'Micr':  # Windows PDB signature
                    self.metadata['format'] = 'Windows PDB'
                    self._parse_windows_pdb(data)
                else:
                    # Try to extract readable strings
                    self._extract_strings(data)
                    
        except Exception as e:
            print(f"Error parsing binary PDB: {e}", file=sys.stderr)
    
    def _parse_portable_pdb(self, data: bytes):
        """Parse Portable PDB format (used by .NET Core)"""
        # Portable PDB format is complex, this is a basic implementation
        # Extract readable strings that might contain useful information
        self._extract_strings(data)
        
        # Look for common patterns
        # Method names often appear as readable strings
        text_data = data.decode('utf-8', errors='ignore')
        
        # Extract potential method names (C# naming conventions)
        method_pattern = r'[A-Z][a-zA-Z0-9_]*\s*\([^)]*\)'
        matches = re.findall(method_pattern, text_data)
        for match in matches[:100]:  # Limit to first 100
            if len(match) > 3 and len(match) < 100:
                self.methods.append({
                    'name': match,
                    'source': 'binary_parse'
                })
    
    def _parse_windows_pdb(self, data: bytes):
        """Parse Windows PDB format"""
        # Windows PDB format is very complex
        # This is a basic implementation that extracts strings
        self._extract_strings(data)
    
    def _extract_strings(self, data: bytes):
        """Extract readable strings from binary data"""
        # Extract UTF-8 and UTF-16 strings
        strings_found = set()
        
        # UTF-8 strings (minimum 4 characters)
        utf8_pattern = rb'[\x20-\x7E]{4,}'
        matches = re.findall(utf8_pattern, data)
        for match in matches:
            try:
                text = match.decode('utf-8')
                if self._is_likely_code_identifier(text):
                    strings_found.add(text)
            except:
                pass
        
        # UTF-16 strings
        utf16_pattern = rb'(?:[\x20-\x7E]\x00){4,}'
        matches = re.findall(utf16_pattern, data)
        for match in matches:
            try:
                text = match.decode('utf-16-le')
                if self._is_likely_code_identifier(text):
                    strings_found.add(text)
            except:
                pass
        
        # Categorize extracted strings
        for text in strings_found:
            if '.' in text and not text.startswith('.'):
                # Might be a namespace or fully qualified name
                parts = text.split('.')
                if len(parts) >= 2:
                    self.namespaces.add('.'.join(parts[:-1]))
                    if text[0].isupper():
                        self.classes.append({
                            'name': text,
                            'namespace': '.'.join(parts[:-1])
                        })
            
            if '(' in text and ')' in text:
                # Might be a method signature
                self.methods.append({
                    'name': text,
                    'source': 'string_extraction'
                })
            
            if text.endswith('.cs') or text.endswith('.vb'):
                # Source file path
                self.source_files.append(text)
    
    def _is_likely_code_identifier(self, text: str) -> bool:
        """Check if a string looks like a code identifier"""
        if len(text) < 2 or len(text) > 200:
            return False
        
        # Should contain mostly alphanumeric and common code characters
        if not re.match(r'^[a-zA-Z0-9_\.\(\)\[\]<>:,\s-]+$', text):
            return False
        
        # Should not be all numbers
        if text.replace('.', '').replace('-', '').isdigit():
            return False
        
        # Common code patterns
        code_patterns = [
            r'^[A-Z][a-zA-Z0-9_]*$',  # PascalCase
            r'^[a-z][a-zA-Z0-9_]*$',  # camelCase
            r'^[A-Z][a-zA-Z0-9_]*\.[A-Z]',  # Namespace.Class
            r'.*\(.*\).*',  # Method signature
        ]
        
        return any(re.match(pattern, text) for pattern in code_patterns)
    
    def parse_cvdump_output(self, output: str):
        """Parse output from cvdump.exe"""
        lines = output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse different sections
            if 'MODULE' in line.upper():
                current_section = 'module'
            elif 'TYPES' in line.upper() or 'SYMBOLS' in line.upper():
                current_section = 'symbols'
            elif 'FILES' in line.upper() or 'SOURCE' in line.upper():
                current_section = 'files'
            
            # Extract method names
            if '(' in line and ')' in line:
                match = re.search(r'([a-zA-Z0-9_\.]+)\s*\([^)]*\)', line)
                if match:
                    method_name = match.group(1)
                    if method_name not in [m['name'] for m in self.methods]:
                        self.methods.append({
                            'name': method_name,
                            'source': 'cvdump',
                            'raw_line': line
                        })
            
            # Extract class names
            if 'class' in line.lower() or 'struct' in line.lower():
                match = re.search(r'(?:class|struct)\s+([a-zA-Z0-9_\.]+)', line, re.IGNORECASE)
                if match:
                    class_name = match.group(1)
                    namespace = '.'.join(class_name.split('.')[:-1]) if '.' in class_name else ''
                    if namespace:
                        self.namespaces.add(namespace)
                    self.classes.append({
                        'name': class_name,
                        'namespace': namespace,
                        'source': 'cvdump'
                    })
            
            # Extract file paths
            if '\\' in line or '/' in line:
                if any(ext in line for ext in ['.cs', '.vb', '.fs', '.cpp', '.h']):
                    if line not in self.source_files:
                        self.source_files.append(line)
    
    def parse_pdb2xml_output(self, output: str):
        """Parse XML output from pdb2xml.exe"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(output)
            
            # Extract namespaces
            for ns_elem in root.findall('.//namespace'):
                ns_name = ns_elem.get('name', '')
                if ns_name:
                    self.namespaces.add(ns_name)
            
            # Extract types/classes
            for type_elem in root.findall('.//type'):
                type_name = type_elem.get('name', '')
                namespace = type_elem.get('namespace', '')
                if type_name:
                    if namespace:
                        self.namespaces.add(namespace)
                    self.types.append({
                        'name': type_name,
                        'namespace': namespace,
                        'kind': type_elem.get('kind', 'unknown')
                    })
            
            # Extract methods
            for method_elem in root.findall('.//method'):
                method_name = method_elem.get('name', '')
                if method_name:
                    self.methods.append({
                        'name': method_name,
                        'source': 'pdb2xml',
                        'class': method_elem.get('class', ''),
                        'namespace': method_elem.get('namespace', '')
                    })
            
            # Extract source files
            for file_elem in root.findall('.//file'):
                file_path = file_elem.get('name', '')
                if file_path:
                    self.source_files.append(file_path)
            
            # Extract line mappings
            for line_elem in root.findall('.//line'):
                self.line_mappings.append({
                    'il_offset': line_elem.get('ilOffset', ''),
                    'line': line_elem.get('line', ''),
                    'file': line_elem.get('file', '')
                })
                
        except Exception as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
            # Fallback to string extraction
            self._extract_strings_from_text(output)
    
    def _extract_strings_from_text(self, text: str):
        """Extract information from plain text output"""
        # Extract namespaces
        namespace_pattern = r'namespace\s+([a-zA-Z0-9_\.]+)'
        for match in re.finditer(namespace_pattern, text, re.IGNORECASE):
            self.namespaces.add(match.group(1))
        
        # Extract class names
        class_pattern = r'(?:public\s+)?(?:class|interface|struct)\s+([a-zA-Z0-9_]+)'
        for match in re.finditer(class_pattern, text, re.IGNORECASE):
            class_name = match.group(1)
            self.classes.append({
                'name': class_name,
                'source': 'text_extraction'
            })
    
    def extract(self):
        """Main extraction method - tries multiple approaches"""
        print(f"Extracting information from: {self.pdb_path}")
        
        # Get file metadata
        stat = self.pdb_path.stat()
        self.metadata = {
            'file_path': str(self.pdb_path),
            'file_size': stat.st_size,
            'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extraction_date': datetime.now().isoformat()
        }
        
        # Try pdb2xml first (best for .NET PDBs)
        xml_output = self.extract_with_pdb2xml()
        if xml_output:
            print("Using pdb2xml.exe for extraction...")
            self.parse_pdb2xml_output(xml_output)
        
        # Try cvdump as fallback
        if not self.methods and not self.classes:
            cvdump_output = self.extract_with_cvdump()
            if cvdump_output:
                print("Using cvdump.exe for extraction...")
                self.parse_cvdump_output(cvdump_output)
        
        # Fallback to binary parsing
        if not self.methods and not self.classes:
            print("Attempting binary parsing...")
            self.parse_binary_pdb()
        
        # Remove duplicates
        self._deduplicate()
    
    def _extract_methods_from_classes(self):
        """Extract method names from class names (especially async state machines)"""
        # Pattern for async state machine classes: <MethodName>d__N
        async_pattern = r'<([^>]+)>d__\d+'
        
        for cls in self.classes:
            class_name = cls.get('name', '')
            # Extract method name from async state machine class names
            match = re.search(async_pattern, class_name)
            if match:
                method_name = match.group(1)
                if method_name not in [m.get('name', '') for m in self.methods]:
                    self.methods.append({
                        'name': method_name,
                        'source': 'class_extraction',
                        'class': class_name,
                        'namespace': cls.get('namespace', '')
                    })
            
            # Also look for other method-like patterns in class names
            # Some obfuscated code might have method signatures in class names
            if '(' in class_name and ')' in class_name:
                # Try to extract method signature
                method_match = re.search(r'([a-zA-Z0-9_<>]+)\s*\([^)]*\)', class_name)
                if method_match:
                    potential_method = method_match.group(0)
                    if len(potential_method) > 3 and len(potential_method) < 200:
                        if potential_method not in [m.get('name', '') for m in self.methods]:
                            self.methods.append({
                                'name': potential_method,
                                'source': 'class_extraction',
                                'class': class_name
                            })
    
    def _deduplicate(self):
        """Remove duplicate entries"""
        # Extract methods from class names first
        self._extract_methods_from_classes()
        
        # Deduplicate methods
        seen_methods = set()
        unique_methods = []
        for method in self.methods:
            method_key = method.get('name', '')
            if method_key and method_key not in seen_methods:
                seen_methods.add(method_key)
                unique_methods.append(method)
        self.methods = unique_methods
        
        # Deduplicate classes
        seen_classes = set()
        unique_classes = []
        for cls in self.classes:
            class_key = cls.get('name', '')
            if class_key and class_key not in seen_classes:
                seen_classes.add(class_key)
                unique_classes.append(cls)
        self.classes = unique_classes
        
        # Deduplicate source files
        self.source_files = list(dict.fromkeys(self.source_files))
    
    def format_output(self) -> str:
        """Format extracted information as readable text"""
        output = []
        
        # Header
        output.append("=" * 80)
        output.append("PDB FILE INFORMATION")
        output.append("=" * 80)
        output.append("")
        output.append(f"File: {self.metadata.get('file_path', 'Unknown')}")
        output.append(f"Size: {self.metadata.get('file_size_mb', 0)} MB ({self.metadata.get('file_size', 0)} bytes)")
        output.append(f"Format: {self.metadata.get('format', 'Unknown')}")
        output.append(f"Modified: {self.metadata.get('modified', 'Unknown')}")
        output.append(f"Extraction Date: {self.metadata.get('extraction_date', 'Unknown')}")
        output.append("")
        
        # Namespaces
        output.append("=" * 80)
        output.append("NAMESPACES")
        output.append("=" * 80)
        if self.namespaces:
            for ns in sorted(self.namespaces):
                output.append(f"  {ns}")
        else:
            output.append("  (No namespaces found)")
        output.append("")
        
        # Classes
        output.append("=" * 80)
        output.append("CLASSES")
        output.append("=" * 80)
        if self.classes:
            for cls in sorted(self.classes, key=lambda x: x.get('name', '')):
                cls_name = cls.get('name', 'Unknown')
                namespace = cls.get('namespace', '')
                if namespace:
                    output.append(f"  {namespace}.{cls_name}")
                else:
                    output.append(f"  {cls_name}")
        else:
            output.append("  (No classes found)")
        output.append("")
        
        # Methods/Functions
        output.append("=" * 80)
        output.append("METHODS/FUNCTIONS")
        output.append("=" * 80)
        if self.methods:
            for method in sorted(self.methods, key=lambda x: x.get('name', '')):
                method_name = method.get('name', 'Unknown')
                source = method.get('source', 'unknown')
                output.append(f"  {method_name} (source: {source})")
        else:
            output.append("  (No methods found)")
        output.append("")
        
        # Source Files
        output.append("=" * 80)
        output.append("SOURCE FILES")
        output.append("=" * 80)
        if self.source_files:
            for file_path in sorted(self.source_files):
                output.append(f"  {file_path}")
        else:
            output.append("  (No source file paths found)")
        output.append("")
        
        # Types
        output.append("=" * 80)
        output.append("TYPES")
        output.append("=" * 80)
        if self.types:
            for type_info in sorted(self.types, key=lambda x: x.get('name', '')):
                type_name = type_info.get('name', 'Unknown')
                namespace = type_info.get('namespace', '')
                kind = type_info.get('kind', 'unknown')
                if namespace:
                    output.append(f"  {namespace}.{type_name} ({kind})")
                else:
                    output.append(f"  {type_name} ({kind})")
        else:
            output.append("  (No type information found)")
        output.append("")
        
        # Line Mappings
        output.append("=" * 80)
        output.append("LINE MAPPINGS")
        output.append("=" * 80)
        if self.line_mappings:
            for mapping in self.line_mappings[:50]:  # Limit to first 50
                il_offset = mapping.get('il_offset', '')
                line = mapping.get('line', '')
                file = mapping.get('file', '')
                output.append(f"  IL Offset: {il_offset} -> Line {line} in {file}")
            if len(self.line_mappings) > 50:
                output.append(f"  ... and {len(self.line_mappings) - 50} more mappings")
        else:
            output.append("  (No line mappings found)")
        output.append("")
        
        # Summary
        output.append("=" * 80)
        output.append("SUMMARY")
        output.append("=" * 80)
        output.append(f"  Namespaces: {len(self.namespaces)}")
        output.append(f"  Classes: {len(self.classes)}")
        output.append(f"  Methods: {len(self.methods)}")
        output.append(f"  Source Files: {len(self.source_files)}")
        output.append(f"  Types: {len(self.types)}")
        output.append(f"  Line Mappings: {len(self.line_mappings)}")
        output.append("")
        
        return '\n'.join(output)
    
    def save(self):
        """Save extracted information to file"""
        output_text = self.format_output()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        
        print(f"\nExtraction complete!")
        print(f"Results saved to: {self.output_path}")
        print(f"\nSummary:")
        print(f"  - Namespaces: {len(self.namespaces)}")
        print(f"  - Classes: {len(self.classes)}")
        print(f"  - Methods: {len(self.methods)}")
        print(f"  - Source Files: {len(self.source_files)}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract information from .NET PDB files'
    )
    parser.add_argument(
        'pdb_file',
        help='Path to the PDB file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: same as PDB file with .txt extension)'
    )
    
    args = parser.parse_args()
    
    try:
        extractor = PDBExtractor(args.pdb_file, args.output)
        extractor.extract()
        extractor.save()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

