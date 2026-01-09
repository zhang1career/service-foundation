from enum import Enum


class ContentTypeEnum(Enum):
    """Content type enumeration for OSS objects"""
    
    # Default/Unknown
    APPLICATION_OCTET_STREAM = 0  # application/octet-stream
    
    # Text types
    TEXT_PLAIN = 1  # text/plain
    TEXT_HTML = 2  # text/html
    TEXT_CSS = 3  # text/css
    TEXT_JAVASCRIPT = 4  # text/javascript
    TEXT_CSV = 5  # text/csv
    TEXT_XML = 6  # text/xml
    
    # Image types
    IMAGE_JPEG = 10  # image/jpeg
    IMAGE_PNG = 11  # image/png
    IMAGE_GIF = 12  # image/gif
    IMAGE_WEBP = 13  # image/webp
    IMAGE_SVG = 14  # image/svg+xml
    IMAGE_BMP = 15  # image/bmp
    IMAGE_ICO = 16  # image/x-icon
    
    # Audio types
    AUDIO_MPEG = 20  # audio/mpeg
    AUDIO_OGG = 21  # audio/ogg
    AUDIO_WAV = 22  # audio/wav
    AUDIO_WEBM = 23  # audio/webm
    
    # Video types
    VIDEO_MP4 = 30  # video/mp4
    VIDEO_OGG = 31  # video/ogg
    VIDEO_WEBM = 32  # video/webm
    VIDEO_QUICKTIME = 33  # video/quicktime
    
    # Application types
    APPLICATION_JSON = 40  # application/json
    APPLICATION_XML = 41  # application/xml
    APPLICATION_PDF = 42  # application/pdf
    APPLICATION_ZIP = 43  # application/zip
    APPLICATION_GZIP = 44  # application/gzip
    APPLICATION_X_TAR = 45  # application/x-tar
    
    # Office document types
    APPLICATION_MSWORD = 50  # application/msword
    APPLICATION_VND_MS_EXCEL = 51  # application/vnd.ms-excel
    APPLICATION_VND_MS_POWERPOINT = 52  # application/vnd.ms-powerpoint
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT = 53  # application/vnd.openxmlformats-officedocument.wordprocessingml.document
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET = 54  # application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION = 55  # application/vnd.openxmlformats-officedocument.presentationml.presentation
    
    @classmethod
    def from_mime_type(cls, mime_type: str) -> 'ContentTypeEnum':
        """
        Convert MIME type string to ContentTypeEnum
        
        Args:
            mime_type: MIME type string (e.g., 'text/plain')
            
        Returns:
            ContentTypeEnum instance, defaults to APPLICATION_OCTET_STREAM if not found
        """
        # Normalize mime_type (lowercase, remove charset)
        mime_type = mime_type.lower().split(';')[0].strip()
        
        # Mapping from MIME type to enum
        mime_to_enum = {
            'application/octet-stream': cls.APPLICATION_OCTET_STREAM,
            'text/plain': cls.TEXT_PLAIN,
            'text/html': cls.TEXT_HTML,
            'text/css': cls.TEXT_CSS,
            'text/javascript': cls.TEXT_JAVASCRIPT,
            'text/csv': cls.TEXT_CSV,
            'text/xml': cls.TEXT_XML,
            'image/jpeg': cls.IMAGE_JPEG,
            'image/jpg': cls.IMAGE_JPEG,
            'image/png': cls.IMAGE_PNG,
            'image/gif': cls.IMAGE_GIF,
            'image/webp': cls.IMAGE_WEBP,
            'image/svg+xml': cls.IMAGE_SVG,
            'image/bmp': cls.IMAGE_BMP,
            'image/x-icon': cls.IMAGE_ICO,
            'audio/mpeg': cls.AUDIO_MPEG,
            'audio/ogg': cls.AUDIO_OGG,
            'audio/wav': cls.AUDIO_WAV,
            'audio/webm': cls.AUDIO_WEBM,
            'video/mp4': cls.VIDEO_MP4,
            'video/ogg': cls.VIDEO_OGG,
            'video/webm': cls.VIDEO_WEBM,
            'video/quicktime': cls.VIDEO_QUICKTIME,
            'application/json': cls.APPLICATION_JSON,
            'application/xml': cls.APPLICATION_XML,
            'application/pdf': cls.APPLICATION_PDF,
            'application/zip': cls.APPLICATION_ZIP,
            'application/gzip': cls.APPLICATION_GZIP,
            'application/x-tar': cls.APPLICATION_X_TAR,
            'application/msword': cls.APPLICATION_MSWORD,
            'application/vnd.ms-excel': cls.APPLICATION_VND_MS_EXCEL,
            'application/vnd.ms-powerpoint': cls.APPLICATION_VND_MS_POWERPOINT,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': cls.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': cls.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': cls.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION,
        }
        
        return mime_to_enum.get(mime_type, cls.APPLICATION_OCTET_STREAM)
    
    def to_mime_type(self) -> str:
        """
        Convert ContentTypeEnum to MIME type string
        
        Returns:
            MIME type string
        """
        enum_to_mime = {
            self.APPLICATION_OCTET_STREAM: 'application/octet-stream',
            self.TEXT_PLAIN: 'text/plain',
            self.TEXT_HTML: 'text/html',
            self.TEXT_CSS: 'text/css',
            self.TEXT_JAVASCRIPT: 'text/javascript',
            self.TEXT_CSV: 'text/csv',
            self.TEXT_XML: 'text/xml',
            self.IMAGE_JPEG: 'image/jpeg',
            self.IMAGE_PNG: 'image/png',
            self.IMAGE_GIF: 'image/gif',
            self.IMAGE_WEBP: 'image/webp',
            self.IMAGE_SVG: 'image/svg+xml',
            self.IMAGE_BMP: 'image/bmp',
            self.IMAGE_ICO: 'image/x-icon',
            self.AUDIO_MPEG: 'audio/mpeg',
            self.AUDIO_OGG: 'audio/ogg',
            self.AUDIO_WAV: 'audio/wav',
            self.AUDIO_WEBM: 'audio/webm',
            self.VIDEO_MP4: 'video/mp4',
            self.VIDEO_OGG: 'video/ogg',
            self.VIDEO_WEBM: 'video/webm',
            self.VIDEO_QUICKTIME: 'video/quicktime',
            self.APPLICATION_JSON: 'application/json',
            self.APPLICATION_XML: 'application/xml',
            self.APPLICATION_PDF: 'application/pdf',
            self.APPLICATION_ZIP: 'application/zip',
            self.APPLICATION_GZIP: 'application/gzip',
            self.APPLICATION_X_TAR: 'application/x-tar',
            self.APPLICATION_MSWORD: 'application/msword',
            self.APPLICATION_VND_MS_EXCEL: 'application/vnd.ms-excel',
            self.APPLICATION_VND_MS_POWERPOINT: 'application/vnd.ms-powerpoint',
            self.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            self.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            self.APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        return enum_to_mime.get(self, 'application/octet-stream')

