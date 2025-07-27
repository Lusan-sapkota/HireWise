"""
File upload optimization and compression utilities for HireWise backend.
Provides efficient file handling, compression, and optimization.
"""

import os
import io
import gzip
import logging
import hashlib
import mimetypes
from typing import Dict, Optional, Tuple, BinaryIO, Any
from pathlib import Path
from datetime import datetime, timedelta

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileOptimizer:
    """
    Comprehensive file optimization and compression utilities.
    """
    
    # Supported file types and their optimization settings
    OPTIMIZATION_SETTINGS = {
        'image': {
            'max_width': 1920,
            'max_height': 1080,
            'quality': 85,
            'format': 'JPEG',
            'progressive': True,
        },
        'pdf': {
            'compress': True,
            'remove_metadata': True,
            'optimize_images': True,
        },
        'document': {
            'compress': True,
            'remove_metadata': True,
        }
    }
    
    # File size limits (in bytes)
    SIZE_LIMITS = {
        'image': 5 * 1024 * 1024,    # 5MB
        'pdf': 10 * 1024 * 1024,     # 10MB
        'document': 5 * 1024 * 1024,  # 5MB
        'default': 10 * 1024 * 1024,  # 10MB
    }
    
    def __init__(self):
        self.temp_dir = Path(settings.MEDIA_ROOT) / 'temp'
        self.temp_dir.mkdir(exist_ok=True)
    
    def optimize_file(self, uploaded_file: UploadedFile) -> Tuple[ContentFile, Dict[str, Any]]:
        """
        Optimize uploaded file based on its type.
        
        Returns:
            Tuple of (optimized_file, optimization_info)
        """
        file_type = self._detect_file_type(uploaded_file)
        original_size = uploaded_file.size
        
        optimization_info = {
            'original_size': original_size,
            'file_type': file_type,
            'optimizations_applied': [],
            'compression_ratio': 0.0,
            'processing_time': 0.0,
        }
        
        start_time = timezone.now()
        
        try:
            if file_type == 'image':
                optimized_file = self._optimize_image(uploaded_file)
                optimization_info['optimizations_applied'].extend([
                    'resize', 'quality_reduction', 'format_conversion'
                ])
            
            elif file_type == 'pdf':
                optimized_file = self._optimize_pdf(uploaded_file)
                optimization_info['optimizations_applied'].extend([
                    'compression', 'metadata_removal'
                ])
            
            elif file_type == 'document':
                optimized_file = self._optimize_document(uploaded_file)
                optimization_info['optimizations_applied'].extend([
                    'compression', 'metadata_removal'
                ])
            
            else:
                # Generic compression for other file types
                optimized_file = self._compress_generic_file(uploaded_file)
                optimization_info['optimizations_applied'].append('generic_compression')
            
            # Calculate optimization metrics
            optimized_size = len(optimized_file.read())
            optimized_file.seek(0)  # Reset file pointer
            
            optimization_info.update({
                'optimized_size': optimized_size,
                'compression_ratio': (original_size - optimized_size) / original_size * 100,
                'processing_time': (timezone.now() - start_time).total_seconds(),
            })
            
            logger.info(f"File optimization completed: {original_size} -> {optimized_size} bytes "
                       f"({optimization_info['compression_ratio']:.1f}% reduction)")
            
            return optimized_file, optimization_info
        
        except Exception as e:
            logger.error(f"File optimization failed: {e}")
            # Return original file if optimization fails
            uploaded_file.seek(0)
            return ContentFile(uploaded_file.read(), name=uploaded_file.name), optimization_info
    
    def _detect_file_type(self, uploaded_file: UploadedFile) -> str:
        """
        Detect file type using magic numbers and MIME type.
        """
        try:
            if MAGIC_AVAILABLE:
                # Read first few bytes for magic number detection
                uploaded_file.seek(0)
                file_header = uploaded_file.read(1024)
                uploaded_file.seek(0)
                
                # Use python-magic for accurate detection
                mime_type = magic.from_buffer(file_header, mime=True)
                
                if mime_type.startswith('image/'):
                    return 'image'
                elif mime_type == 'application/pdf':
                    return 'pdf'
                elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    return 'document'
                else:
                    return 'other'
        
        except Exception as e:
            logger.warning(f"File type detection failed: {e}")
        
        # Fallback to file extension
        if uploaded_file.name:
            ext = Path(uploaded_file.name).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return 'image'
            elif ext == '.pdf':
                return 'pdf'
            elif ext in ['.doc', '.docx']:
                return 'document'
        
        return 'other'
    
    def _optimize_image(self, uploaded_file: UploadedFile) -> ContentFile:
        """
        Optimize image files with compression and resizing.
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, using generic compression for image")
            return self._compress_generic_file(uploaded_file)
        
        try:
            settings_img = self.OPTIMIZATION_SETTINGS['image']
            
            # Open image with PIL
            image = Image.open(uploaded_file)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize if too large
            if image.width > settings_img['max_width'] or image.height > settings_img['max_height']:
                image.thumbnail(
                    (settings_img['max_width'], settings_img['max_height']),
                    Image.Resampling.LANCZOS
                )
            
            # Save optimized image
            output = io.BytesIO()
            image.save(
                output,
                format=settings_img['format'],
                quality=settings_img['quality'],
                optimize=True,
                progressive=settings_img['progressive']
            )
            
            output.seek(0)
            return ContentFile(output.read(), name=uploaded_file.name)
        
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return self._compress_generic_file(uploaded_file)
    
    def _optimize_pdf(self, uploaded_file: UploadedFile) -> ContentFile:
        """
        Optimize PDF files with compression.
        """
        if not PYPDF2_AVAILABLE:
            logger.warning("PyPDF2 not available, using generic compression for PDF")
            return self._compress_generic_file(uploaded_file)
        
        try:
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy pages with optimization
            for page in pdf_reader.pages:
                # Remove metadata and compress
                page.compress_content_streams()
                pdf_writer.add_page(page)
            
            # Remove metadata
            pdf_writer.add_metadata({})
            
            # Write optimized PDF
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            return ContentFile(output.read(), name=uploaded_file.name)
        
        except Exception as e:
            logger.error(f"PDF optimization failed: {e}")
            # Return compressed version using gzip
            return self._compress_generic_file(uploaded_file)
    
    def _optimize_document(self, uploaded_file: UploadedFile) -> ContentFile:
        """
        Optimize document files (DOCX, etc.).
        """
        try:
            if uploaded_file.name.endswith('.docx') and DOCX_AVAILABLE:
                # Open DOCX document
                doc = Document(uploaded_file)
                
                # Remove metadata
                core_props = doc.core_properties
                core_props.author = ''
                core_props.comments = ''
                core_props.keywords = ''
                core_props.subject = ''
                core_props.title = ''
                
                # Save optimized document
                output = io.BytesIO()
                doc.save(output)
                output.seek(0)
                
                return ContentFile(output.read(), name=uploaded_file.name)
            
            else:
                # Generic compression for other document types
                return self._compress_generic_file(uploaded_file)
        
        except Exception as e:
            logger.error(f"Document optimization failed: {e}")
            return self._compress_generic_file(uploaded_file)
    
    def _compress_generic_file(self, uploaded_file: UploadedFile) -> ContentFile:
        """
        Apply generic compression to any file type.
        """
        uploaded_file.seek(0)
        original_data = uploaded_file.read()
        
        # Compress with gzip
        compressed_data = gzip.compress(original_data, compresslevel=6)
        
        # Only use compressed version if it's actually smaller
        if len(compressed_data) < len(original_data):
            return ContentFile(compressed_data, name=f"{uploaded_file.name}.gz")
        else:
            return ContentFile(original_data, name=uploaded_file.name)


class FileUploadManager:
    """
    Manages file uploads with optimization, validation, and caching.
    """
    
    def __init__(self):
        self.optimizer = FileOptimizer()
        self.cache_timeout = 3600  # 1 hour
    
    def process_upload(
        self,
        uploaded_file: UploadedFile,
        user_id: str,
        file_category: str = 'general'
    ) -> Dict[str, Any]:
        """
        Process file upload with optimization and validation.
        
        Returns:
            Dictionary with file information and processing results
        """
        processing_start = timezone.now()
        
        # Generate file hash for deduplication
        file_hash = self._calculate_file_hash(uploaded_file)
        
        # Check if file already exists (deduplication)
        cached_result = self._get_cached_file_result(file_hash)
        if cached_result:
            logger.info(f"File deduplication hit for hash: {file_hash}")
            return cached_result
        
        # Validate file
        validation_result = self._validate_file(uploaded_file, file_category)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'file_hash': file_hash,
            }
        
        try:
            # Optimize file
            optimized_file, optimization_info = self.optimizer.optimize_file(uploaded_file)
            
            # Generate unique filename
            filename = self._generate_unique_filename(
                uploaded_file.name, user_id, file_category
            )
            
            # Save optimized file
            file_path = default_storage.save(filename, optimized_file)
            file_url = default_storage.url(file_path)
            
            # Prepare result
            result = {
                'success': True,
                'file_path': file_path,
                'file_url': file_url,
                'file_hash': file_hash,
                'original_filename': uploaded_file.name,
                'file_size': optimization_info['optimized_size'],
                'original_size': optimization_info['original_size'],
                'compression_ratio': optimization_info['compression_ratio'],
                'file_type': optimization_info['file_type'],
                'optimizations_applied': optimization_info['optimizations_applied'],
                'processing_time': (timezone.now() - processing_start).total_seconds(),
                'uploaded_at': timezone.now().isoformat(),
            }
            
            # Cache result for deduplication
            self._cache_file_result(file_hash, result)
            
            logger.info(f"File upload processed successfully: {filename}")
            return result
        
        except Exception as e:
            logger.error(f"File upload processing failed: {e}")
            return {
                'success': False,
                'error': f"File processing failed: {str(e)}",
                'file_hash': file_hash,
            }
    
    def _calculate_file_hash(self, uploaded_file: UploadedFile) -> str:
        """
        Calculate SHA-256 hash of file content for deduplication.
        """
        uploaded_file.seek(0)
        file_hash = hashlib.sha256()
        
        # Read file in chunks to handle large files
        for chunk in iter(lambda: uploaded_file.read(8192), b''):
            file_hash.update(chunk)
        
        uploaded_file.seek(0)  # Reset file pointer
        return file_hash.hexdigest()
    
    def _validate_file(self, uploaded_file: UploadedFile, file_category: str) -> Dict[str, Any]:
        """
        Validate uploaded file against security and size constraints.
        """
        # Check file size
        max_size = FileOptimizer.SIZE_LIMITS.get(file_category, FileOptimizer.SIZE_LIMITS['default'])
        if uploaded_file.size > max_size:
            return {
                'valid': False,
                'error': f'File size ({uploaded_file.size} bytes) exceeds limit ({max_size} bytes)'
            }
        
        # Check file extension
        if uploaded_file.name:
            ext = Path(uploaded_file.name).suffix.lower()
            allowed_extensions = getattr(settings, 'SECURE_FILE_UPLOAD', {}).get(
                'ALLOWED_EXTENSIONS', ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            )
            
            if ext not in allowed_extensions:
                return {
                    'valid': False,
                    'error': f'File extension {ext} not allowed'
                }
        
        # Check MIME type if magic is available
        if MAGIC_AVAILABLE:
            try:
                uploaded_file.seek(0)
                file_header = uploaded_file.read(1024)
                uploaded_file.seek(0)
                
                mime_type = magic.from_buffer(file_header, mime=True)
                
                # Define allowed MIME types
                allowed_mime_types = [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain',
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                ]
                
                if mime_type not in allowed_mime_types:
                    return {
                        'valid': False,
                        'error': f'MIME type {mime_type} not allowed'
                    }
            
            except Exception as e:
                logger.warning(f"MIME type validation failed: {e}")
        
        return {'valid': True}
    
    def _generate_unique_filename(self, original_name: str, user_id: str, category: str) -> str:
        """
        Generate unique filename with user ID and timestamp.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_part = Path(original_name).stem[:50]  # Limit name length
        extension = Path(original_name).suffix
        
        # Create user-specific directory structure
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        
        return f"{category}/{user_hash}/{timestamp}_{name_part}{extension}"
    
    def _get_cached_file_result(self, file_hash: str) -> Optional[Dict]:
        """
        Get cached file processing result for deduplication.
        """
        cache_key = f"file_upload:{file_hash}"
        return cache.get(cache_key)
    
    def _cache_file_result(self, file_hash: str, result: Dict):
        """
        Cache file processing result for deduplication.
        """
        cache_key = f"file_upload:{file_hash}"
        cache.set(cache_key, result, self.cache_timeout)


class FileCleanupManager:
    """
    Manages cleanup of temporary and old files.
    """
    
    @staticmethod
    def cleanup_temp_files(max_age_hours: int = 24):
        """
        Clean up temporary files older than specified age.
        """
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp'
        if not temp_dir.exists():
            return
        
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        try:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if timezone.make_aware(file_mtime) < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        
        except Exception as e:
            logger.error(f"Temporary file cleanup failed: {e}")
    
    @staticmethod
    def cleanup_orphaned_files():
        """
        Clean up files that are no longer referenced in the database.
        """
        from .models import Resume
        
        try:
            # Get all file paths from database
            db_files = set(Resume.objects.values_list('file', flat=True))
            
            # Get all files in media directory
            media_root = Path(settings.MEDIA_ROOT)
            actual_files = set()
            
            for file_path in media_root.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(media_root)
                    actual_files.add(str(relative_path))
            
            # Find orphaned files
            orphaned_files = actual_files - db_files
            cleaned_count = 0
            
            for orphaned_file in orphaned_files:
                file_path = media_root / orphaned_file
                if file_path.exists():
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} orphaned files")
        
        except Exception as e:
            logger.error(f"Orphaned file cleanup failed: {e}")


# Utility functions for file optimization

def optimize_uploaded_file(uploaded_file: UploadedFile) -> Tuple[ContentFile, Dict]:
    """
    Convenience function to optimize a single uploaded file.
    """
    optimizer = FileOptimizer()
    return optimizer.optimize_file(uploaded_file)


def process_file_upload(uploaded_file: UploadedFile, user_id: str, category: str = 'general') -> Dict:
    """
    Convenience function to process file upload with all optimizations.
    """
    manager = FileUploadManager()
    return manager.process_upload(uploaded_file, user_id, category)


def get_file_optimization_stats() -> Dict[str, Any]:
    """
    Get file optimization statistics from cache.
    """
    # This would aggregate optimization statistics
    return {
        'total_files_processed': 0,
        'total_bytes_saved': 0,
        'average_compression_ratio': 0.0,
        'most_optimized_file_type': 'image',
    }