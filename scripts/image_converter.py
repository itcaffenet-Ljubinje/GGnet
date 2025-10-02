#!/usr/bin/env python3
"""
Image Conversion Script for GGnet Diskless Server

This script provides functions to convert between different disk image formats
using qemu-img and other tools.
"""

import subprocess
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageConversionError(Exception):
    """Custom exception for image conversion operations"""
    pass


class ImageConverter:
    """Manager class for image conversion operations"""
    
    def __init__(self, qemu_img_path: str = "/usr/bin/qemu-img", mock_mode: bool = False):
        self.qemu_img_path = qemu_img_path
        self.mock_mode = mock_mode
        
        if not mock_mode and not Path(qemu_img_path).exists():
            raise ImageConversionError(f"qemu-img not found at {qemu_img_path}")
        
        # Supported formats
        self.supported_formats = {
            'vhd': 'vpc',      # VHD format (Virtual PC)
            'vhdx': 'vhdx',    # VHDX format (Hyper-V)
            'raw': 'raw',      # Raw disk image
            'qcow2': 'qcow2',  # QEMU Copy-On-Write v2
            'vmdk': 'vmdk',    # VMware disk format
            'vdi': 'vdi'       # VirtualBox disk format
        }
    
    def _run_command(self, cmd: List[str], timeout: int = 3600) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr)"""
        if self.mock_mode:
            logger.info(f"MOCK: Would run command: {' '.join(cmd)}")
            return 0, "Mock command executed successfully", ""
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            raise ImageConversionError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        except Exception as e:
            raise ImageConversionError(f"Failed to execute command: {e}")
    
    def get_image_info(self, image_path: str) -> Dict:
        """Get information about an image file"""
        try:
            if not Path(image_path).exists():
                raise ImageConversionError(f"Image file not found: {image_path}")
            
            cmd = [self.qemu_img_path, "info", "--output=json", image_path]
            returncode, stdout, stderr = self._run_command(cmd, timeout=60)
            
            if returncode != 0:
                raise ImageConversionError(f"Failed to get image info: {stderr}")
            
            info = json.loads(stdout)
            
            # Add file size
            file_size = Path(image_path).stat().st_size
            info['file_size'] = file_size
            info['file_size_mb'] = round(file_size / (1024 * 1024), 2)
            info['file_size_gb'] = round(file_size / (1024 * 1024 * 1024), 2)
            
            return info
            
        except json.JSONDecodeError as e:
            raise ImageConversionError(f"Failed to parse qemu-img output: {e}")
        except Exception as e:
            raise ImageConversionError(f"Failed to get image info: {e}")
    
    def validate_format(self, format_name: str) -> str:
        """Validate and normalize format name"""
        format_name = format_name.lower()
        if format_name not in self.supported_formats:
            raise ImageConversionError(
                f"Unsupported format: {format_name}. "
                f"Supported formats: {', '.join(self.supported_formats.keys())}"
            )
        return self.supported_formats[format_name]
    
    def convert_image(
        self,
        source_path: str,
        target_path: str,
        target_format: str,
        compress: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """Convert image from one format to another"""
        try:
            # Validate inputs
            if not Path(source_path).exists():
                raise ImageConversionError(f"Source image not found: {source_path}")
            
            target_format_qemu = self.validate_format(target_format)
            
            # Get source image info
            source_info = self.get_image_info(source_path)
            logger.info(f"Converting {source_info['format']} to {target_format}")
            logger.info(f"Source size: {source_info['file_size_gb']} GB")
            
            # Prepare conversion command
            cmd = [
                self.qemu_img_path, "convert",
                "-f", source_info['format'],
                "-O", target_format_qemu
            ]
            
            # Add compression if requested and supported
            if compress and target_format_qemu in ['qcow2', 'vmdk']:
                cmd.extend(["-c"])
                logger.info("Compression enabled")
            
            # Add progress monitoring
            cmd.extend(["-p"])
            
            # Add source and target
            cmd.extend([source_path, target_path])
            
            # Create target directory if needed
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Run conversion
            logger.info(f"Starting conversion: {source_path} -> {target_path}")
            returncode, stdout, stderr = self._run_command(cmd, timeout=7200)  # 2 hour timeout
            
            if returncode != 0:
                # Clean up failed conversion
                if Path(target_path).exists():
                    Path(target_path).unlink()
                raise ImageConversionError(f"Conversion failed: {stderr}")
            
            # Get target image info
            target_info = self.get_image_info(target_path)
            
            # Calculate compression ratio
            compression_ratio = 1.0
            if source_info['file_size'] > 0:
                compression_ratio = target_info['file_size'] / source_info['file_size']
            
            result = {
                "source_path": source_path,
                "target_path": target_path,
                "source_format": source_info['format'],
                "target_format": target_format,
                "source_size_bytes": source_info['file_size'],
                "target_size_bytes": target_info['file_size'],
                "source_size_gb": source_info['file_size_gb'],
                "target_size_gb": target_info['file_size_gb'],
                "compression_ratio": round(compression_ratio, 3),
                "space_saved_bytes": source_info['file_size'] - target_info['file_size'],
                "compressed": compress,
                "virtual_size": target_info.get('virtual-size', 0)
            }
            
            logger.info(f"Conversion completed successfully")
            logger.info(f"Target size: {result['target_size_gb']} GB")
            logger.info(f"Compression ratio: {result['compression_ratio']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            # Clean up on failure
            if Path(target_path).exists():
                try:
                    Path(target_path).unlink()
                except:
                    pass
            raise ImageConversionError(f"Conversion failed: {e}")
    
    def resize_image(self, image_path: str, new_size: str) -> bool:
        """Resize an image (expand only for safety)"""
        try:
            if not Path(image_path).exists():
                raise ImageConversionError(f"Image file not found: {image_path}")
            
            # Get current size
            info = self.get_image_info(image_path)
            current_size = info.get('virtual-size', 0)
            
            cmd = [self.qemu_img_path, "resize", image_path, new_size]
            returncode, stdout, stderr = self._run_command(cmd, timeout=300)
            
            if returncode != 0:
                raise ImageConversionError(f"Failed to resize image: {stderr}")
            
            logger.info(f"Resized image {image_path} to {new_size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            raise ImageConversionError(f"Resize failed: {e}")
    
    def create_snapshot(self, base_image: str, snapshot_path: str) -> bool:
        """Create a qcow2 snapshot based on another image"""
        try:
            if not Path(base_image).exists():
                raise ImageConversionError(f"Base image not found: {base_image}")
            
            cmd = [
                self.qemu_img_path, "create",
                "-f", "qcow2",
                "-b", base_image,
                "-F", "raw",  # Assume base is raw, adjust as needed
                snapshot_path
            ]
            
            returncode, stdout, stderr = self._run_command(cmd, timeout=300)
            
            if returncode != 0:
                raise ImageConversionError(f"Failed to create snapshot: {stderr}")
            
            logger.info(f"Created snapshot: {snapshot_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise ImageConversionError(f"Snapshot creation failed: {e}")
    
    def check_image_integrity(self, image_path: str) -> Dict:
        """Check image integrity"""
        try:
            if not Path(image_path).exists():
                raise ImageConversionError(f"Image file not found: {image_path}")
            
            cmd = [self.qemu_img_path, "check", "--output=json", image_path]
            returncode, stdout, stderr = self._run_command(cmd, timeout=600)
            
            # qemu-img check returns non-zero for corrupted images
            result = {
                "path": image_path,
                "is_valid": returncode == 0,
                "errors": [],
                "warnings": []
            }
            
            if stdout:
                try:
                    check_result = json.loads(stdout)
                    result.update(check_result)
                except json.JSONDecodeError:
                    result["raw_output"] = stdout
            
            if stderr:
                result["stderr"] = stderr
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check image integrity: {e}")
            return {
                "path": image_path,
                "is_valid": False,
                "errors": [str(e)]
            }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported formats"""
        try:
            cmd = [self.qemu_img_path, "--help"]
            returncode, stdout, stderr = self._run_command(cmd, timeout=30)
            
            if returncode != 0:
                return list(self.supported_formats.keys())
            
            # Parse supported formats from help output
            # This is a basic implementation
            return list(self.supported_formats.keys())
            
        except Exception:
            return list(self.supported_formats.keys())


def main():
    """Command line interface for image converter"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GGnet Image Converter")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--qemu-img", default="/usr/bin/qemu-img", help="Path to qemu-img binary")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert image format")
    convert_parser.add_argument("source", help="Source image file")
    convert_parser.add_argument("target", help="Target image file")
    convert_parser.add_argument("format", help="Target format (vhd, vhdx, raw, qcow2, vmdk, vdi)")
    convert_parser.add_argument("--compress", action="store_true", help="Enable compression")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get image information")
    info_parser.add_argument("image", help="Image file path")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check image integrity")
    check_parser.add_argument("image", help="Image file path")
    
    # Resize command
    resize_parser = subparsers.add_parser("resize", help="Resize image")
    resize_parser.add_argument("image", help="Image file path")
    resize_parser.add_argument("size", help="New size (e.g., +10G, 50G)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        converter = ImageConverter(qemu_img_path=args.qemu_img, mock_mode=args.mock)
        
        if args.command == "convert":
            result = converter.convert_image(
                source_path=args.source,
                target_path=args.target,
                target_format=args.format,
                compress=args.compress
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == "info":
            info = converter.get_image_info(args.image)
            print(json.dumps(info, indent=2))
            
        elif args.command == "check":
            result = converter.check_image_integrity(args.image)
            print(json.dumps(result, indent=2))
            
        elif args.command == "resize":
            converter.resize_image(args.image, args.size)
            print(f"Resized {args.image} to {args.size}")
            
        return 0
        
    except ImageConversionError as e:
        logger.error(f"Image conversion failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

