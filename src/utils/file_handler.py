"""
File handling utilities for PowerFactory network analysis.
"""

import json
import yaml
import csv
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime

from .logger import AnalysisLogger


class FileHandler:
    """
    Utility class for file I/O operations.
    
    Provides standardized methods for reading and writing various file formats
    used in the PowerFactory analysis workflow.
    """
    
    def __init__(self):
        """Initialize file handler."""
        self.logger = AnalysisLogger(self.__class__.__name__)
    
    def read_yaml(self, filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read YAML configuration file.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Dictionary with configuration data or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self.logger.debug(f"Successfully read YAML file: {filepath}")
            return data
            
        except FileNotFoundError:
            self.logger.error(f"YAML file not found: {filepath}")
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading YAML file {filepath}: {e}")
        
        return None
    
    def write_yaml(self, data: Dict[str, Any], filepath: Union[str, Path]) -> bool:
        """
        Write data to YAML file.
        
        Args:
            data: Dictionary to write
            filepath: Output file path
            
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            
            self.logger.debug(f"Successfully wrote YAML file: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing YAML file {filepath}: {e}")
            return False
    
    def read_json(self, filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dictionary with data or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.debug(f"Successfully read JSON file: {filepath}")
            return data
            
        except FileNotFoundError:
            self.logger.error(f"JSON file not found: {filepath}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON file {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading JSON file {filepath}: {e}")
        
        return None
    
    def write_json(self, data: Any, filepath: Union[str, Path], indent: int = 2) -> bool:
        """
        Write data to JSON file.
        
        Args:
            data: Data to write
            filepath: Output file path
            indent: JSON indentation
            
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
            
            self.logger.debug(f"Successfully wrote JSON file: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing JSON file {filepath}: {e}")
            return False
    
    def read_csv(self, filepath: Union[str, Path], 
                 has_header: bool = True, 
                 delimiter: str = ',') -> Optional[List[Dict[str, Any]]]:
        """
        Read CSV file.
        
        Args:
            filepath: Path to CSV file
            has_header: Whether CSV has header row
            delimiter: CSV delimiter
            
        Returns:
            List of dictionaries or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if has_header:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    data = list(reader)
                else:
                    reader = csv.reader(f, delimiter=delimiter)
                    data = [{'col' + str(i): value for i, value in enumerate(row)} 
                           for row in reader]
            
            self.logger.debug(f"Successfully read CSV file: {filepath} ({len(data)} rows)")
            return data
            
        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {filepath}")
        except Exception as e:
            self.logger.error(f"Error reading CSV file {filepath}: {e}")
        
        return None
    
    def write_csv(self, data: List[Dict[str, Any]], 
                  filepath: Union[str, Path],
                  delimiter: str = ',',
                  write_header: bool = True) -> bool:
        """
        Write data to CSV file.
        
        Args:
            data: List of dictionaries to write
            filepath: Output file path
            delimiter: CSV delimiter
            write_header: Whether to write header row
            
        Returns:
            True if successful
        """
        try:
            if not data:
                self.logger.warning(f"No data to write to CSV: {filepath}")
                return True
            
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                
                if write_header:
                    writer.writeheader()
                writer.writerows(data)
            
            self.logger.debug(f"Successfully wrote CSV file: {filepath} ({len(data)} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing CSV file {filepath}: {e}")
            return False
    
    def ensure_directory(self, dirpath: Union[str, Path]) -> bool:
        """
        Ensure directory exists.
        
        Args:
            dirpath: Directory path
            
        Returns:
            True if directory exists or was created
        """
        try:
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error creating directory {dirpath}: {e}")
            return False
    
    def backup_file(self, filepath: Union[str, Path], 
                    backup_suffix: Optional[str] = None) -> Optional[Path]:
        """
        Create backup of file.
        
        Args:
            filepath: File to backup
            backup_suffix: Suffix for backup file (default: timestamp)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            source_path = Path(filepath)
            
            if not source_path.exists():
                self.logger.warning(f"File to backup does not exist: {filepath}")
                return None
            
            if backup_suffix is None:
                backup_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            backup_path = source_path.with_suffix(f'.{backup_suffix}{source_path.suffix}')
            
            # Copy file
            import shutil
            shutil.copy2(source_path, backup_path)
            
            self.logger.debug(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup of {filepath}: {e}")
            return None
    
    def cleanup_old_files(self, directory: Union[str, Path], 
                         pattern: str = "*", 
                         max_age_days: int = 30) -> int:
        """
        Clean up old files in directory.
        
        Args:
            directory: Directory to clean
            pattern: File pattern to match
            max_age_days: Maximum age in days
            
        Returns:
            Number of files deleted
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            deleted_count = 0
            
            for file_path in dir_path.glob(pattern):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.debug(f"Deleted old file: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not delete file {file_path}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old files from {directory}")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up files in {directory}: {e}")
            return 0
    
    def get_file_info(self, filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Get file information.
        
        Args:
            filepath: Path to file
            
        Returns:
            Dictionary with file information or None if failed
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            info = {
                'name': file_path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir(),
                'extension': file_path.suffix,
                'absolute_path': str(file_path.absolute())
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {filepath}: {e}")
            return None
    
    def copy_file(self, source: Union[str, Path], 
                  destination: Union[str, Path]) -> bool:
        """
        Copy file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            import shutil
            
            # Ensure destination directory exists
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            self.logger.debug(f"Copied file: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying file {source} to {destination}: {e}")
            return False
    
    def move_file(self, source: Union[str, Path], 
                  destination: Union[str, Path]) -> bool:
        """
        Move file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            import shutil
            
            # Ensure destination directory exists
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source, destination)
            self.logger.debug(f"Moved file: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {e}")
            return False
    
    def archive_directory(self, directory: Union[str, Path], 
                         archive_path: Union[str, Path],
                         format: str = 'zip') -> bool:
        """
        Create archive of directory.
        
        Args:
            directory: Directory to archive
            archive_path: Path for archive file
            format: Archive format ('zip', 'tar', 'gztar')
            
        Returns:
            True if successful
        """
        try:
            import shutil
            
            # Ensure archive directory exists
            archive_path = Path(archive_path)
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove extension if present (shutil.make_archive adds it)
            if archive_path.suffix:
                base_name = str(archive_path.with_suffix(''))
            else:
                base_name = str(archive_path)
            
            shutil.make_archive(base_name, format, directory)
            self.logger.info(f"Created archive: {base_name}.{format}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating archive of {directory}: {e}")
            return False
    
    def read_text_file(self, filepath: Union[str, Path], 
                      encoding: str = 'utf-8') -> Optional[str]:
        """
        Read text file content.
        
        Args:
            filepath: Path to text file
            encoding: File encoding
            
        Returns:
            File content as string or None if failed
        """
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            self.logger.debug(f"Successfully read text file: {filepath}")
            return content
            
        except FileNotFoundError:
            self.logger.error(f"Text file not found: {filepath}")
        except Exception as e:
            self.logger.error(f"Error reading text file {filepath}: {e}")
        
        return None
    
    def write_text_file(self, content: str, 
                       filepath: Union[str, Path],
                       encoding: str = 'utf-8') -> bool:
        """
        Write content to text file.
        
        Args:
            content: Text content to write
            filepath: Output file path
            encoding: File encoding
            
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
            
            self.logger.debug(f"Successfully wrote text file: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing text file {filepath}: {e}")
            return False
