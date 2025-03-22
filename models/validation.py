import os
from utils.logger import logging

def FileValidation(file, FileSize=20, extension=['.jpg', '.png', '.jpeg', '.webp']):
    try:
        # Extension validation
        if hasattr(file, 'name'):
            ext = os.path.splitext(file.filename)[1].lower()

        else:
            return {'success': False, 'message': 'Unable to determine file extension.'}

        if ext not in extension:
            return {'success': False, 'message': f'Only {", ".join(extension)} files are allowed.'}
        
        # Get file size
        if hasattr(file, 'size'):
            file_size = file.size
        elif hasattr(file, 'seek') and hasattr(file, 'tell'):
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer to the beginning
        else:
            return {'success': False, 'message': 'Unable to determine file size.'}

        # Size validation (max size in MB)
        if file_size / (1024 * 1024) > FileSize:
            return {'success': False, 'message': f'Max size should be {FileSize}MB.'}
        
        return {'success': True}
    
    except Exception as e:
        logging.error(str(e))
        return {'success': False, 'message': str(e)}