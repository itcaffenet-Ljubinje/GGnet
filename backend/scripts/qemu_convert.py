#!/usr/bin/env python3
"""
qemu-img wrapper script for image format conversion
Supports VHDX to RAW conversion for iSCSI targets
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QemuImageConverter:
    """Wrapper for qemu-img conversion operations"""
    
    def __init__(self, qemu_img_path: str = "qemu-img"):
        self.qemu_img_path = qemu_img_path
        self._check_qemu_img()
    
    def _check_qemu_img(self) -> bool:
        """Check if qemu-img is available"""
        try:
            result = subprocess.run(
                [self.qemu_img_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"qemu-img found: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"qemu-img check failed: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"qemu-img not found: {e}")
            return False
    
    async def get_image_info(self, image_path: str) -> Dict:
        """Get image information using qemu-img info"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.qemu_img_path, "info", "--output=json", image_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                info = json.loads(stdout.decode())
                logger.info(f"Image info retrieved for {image_path}")
                return info
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to get image info: {error_msg}")
                raise RuntimeError(f"qemu-img info failed: {error_msg}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse qemu-img info JSON: {e}")
            raise RuntimeError(f"Invalid JSON from qemu-img info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting image info: {e}")
            raise
    
    async def convert_image(
        self,
        input_path: str,
        output_path: str,
        output_format: str = "raw",
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Convert image from one format to another
        
        Args:
            input_path: Path to input image
            output_path: Path to output image
            output_format: Output format (raw, qcow2, vmdk, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with conversion results
        """
        logger.info(f"Starting conversion: {input_path} -> {output_path} ({output_format})")
        
        # Validate input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Get input image info
        try:
            input_info = await self.get_image_info(input_path)
            input_size = input_info.get("virtual-size", 0)
            logger.info(f"Input image size: {input_size} bytes ({input_size / (1024**3):.2f} GB)")
        except Exception as e:
            logger.warning(f"Could not get input image info: {e}")
            input_info = {}
            input_size = 0
        
        # Prepare conversion command
        cmd = [
            self.qemu_img_path, "convert",
            "-f", "auto",  # Auto-detect input format
            "-O", output_format,
            "-p",  # Show progress
            input_path,
            output_path
        ]
        
        # Add sparse file option for raw format
        if output_format == "raw":
            cmd.extend(["-S", "0"])  # Create sparse file
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start conversion process
        start_time = asyncio.get_event_loop().time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress if callback provided
            if progress_callback:
                await self._monitor_progress(process, progress_callback, input_size)
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # Get output file info
                try:
                    output_info = await self.get_image_info(output_path)
                    output_size = output_info.get("virtual-size", 0)
                except Exception:
                    output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                
                result = {
                    "success": True,
                    "input_path": input_path,
                    "output_path": output_path,
                    "input_format": input_info.get("format", "unknown"),
                    "output_format": output_format,
                    "input_size": input_size,
                    "output_size": output_size,
                    "duration_seconds": duration,
                    "compression_ratio": output_size / input_size if input_size > 0 else 0
                }
                
                logger.info(f"Conversion completed successfully in {duration:.2f} seconds")
                logger.info(f"Output size: {output_size} bytes ({output_size / (1024**3):.2f} GB)")
                
                return result
                
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Conversion failed: {error_msg}")
                raise RuntimeError(f"qemu-img convert failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            # Clean up partial output file
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info(f"Cleaned up partial output file: {output_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up partial file: {cleanup_error}")
            raise
    
    async def _monitor_progress(
        self,
        process: asyncio.subprocess.Process,
        progress_callback: callable,
        total_size: int
    ):
        """Monitor conversion progress and call progress callback"""
        try:
            while process.returncode is None:
                # Read stderr for progress information
                if process.stderr:
                    line = await process.stderr.readline()
                    if line:
                        line_str = line.decode().strip()
                        # Parse qemu-img progress output
                        if "(" in line_str and "%)" in line_str:
                            try:
                                # Extract percentage from line like "Progress: 45.2% (123456789/987654321)"
                                percent_str = line_str.split("(")[1].split("%")[0]
                                percent = float(percent_str)
                                progress_callback(percent, total_size)
                            except (ValueError, IndexError):
                                pass
                
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"Progress monitoring error: {e}")
    
    async def create_sparse_file(self, path: str, size_bytes: int) -> bool:
        """Create a sparse file of specified size"""
        try:
            logger.info(f"Creating sparse file: {path} ({size_bytes} bytes)")
            
            # Create parent directory
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Use truncate to create sparse file
            with open(path, 'wb') as f:
                f.truncate(size_bytes)
            
            logger.info(f"Sparse file created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sparse file: {e}")
            return False
    
    async def resize_image(self, image_path: str, new_size: str) -> bool:
        """Resize an image to new size (e.g., '10G', '500M')"""
        try:
            logger.info(f"Resizing image {image_path} to {new_size}")
            
            cmd = [self.qemu_img_path, "resize", image_path, new_size]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info(f"Image resized successfully")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Resize failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Resize error: {e}")
            return False


async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="qemu-img wrapper for image conversion")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument("-f", "--format", default="raw", help="Output format (default: raw)")
    parser.add_argument("--qemu-img", default="qemu-img", help="Path to qemu-img binary")
    parser.add_argument("--info", action="store_true", help="Show image info only")
    parser.add_argument("--resize", help="Resize image to specified size (e.g., '10G')")
    
    args = parser.parse_args()
    
    converter = QemuImageConverter(args.qemu_img)
    
    try:
        if args.info:
            # Show image info
            info = await converter.get_image_info(args.input)
            print(json.dumps(info, indent=2))
            
        elif args.resize:
            # Resize image
            success = await converter.resize_image(args.input, args.resize)
            sys.exit(0 if success else 1)
            
        else:
            # Convert image
            def progress_callback(percent: float, total_size: int):
                print(f"Progress: {percent:.1f}% ({total_size / (1024**3):.2f} GB)")
            
            result = await converter.convert_image(
                args.input,
                args.output,
                args.format,
                progress_callback
            )
            
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
