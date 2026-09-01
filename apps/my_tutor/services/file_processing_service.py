import io
import base64
import docx
import PyPDF2
import logging

logger = logging.getLogger(__name__)

class FileProcessingService:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, file_type: str, max_chars: int = 35000) -> str:
        """
        Extract text from PDF, DOCX, or TXT file bytes and truncate if it exceeds max_chars.
        """
        try:
            file_type = file_type.lower().strip('.')
            if file_type == 'pdf':
                text = FileProcessingService._extract_pdf(file_bytes, max_chars=max_chars)
            elif file_type in ['docx', 'doc']:
                text = FileProcessingService._extract_docx(file_bytes)
            elif file_type == 'txt':
                text = FileProcessingService._extract_txt(file_bytes)
            else:
                return f"[Note: Unsupported document file type '{file_type}']"
            
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[TRUNCATED: The uploaded document is too large. Showing only the first {max_chars} characters to preserve chat memory and token limits.]"
            return text
        except BaseException as b_err:
            logger.error(f"Critical error extracting text from {file_type}: {b_err}")
            return f"[Note: Error reading {file_type} document content.]"

    @staticmethod
    def _extract_pdf(file_bytes: bytes, max_chars: int = 35000) -> str:
        text = ""
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PyPDF2.PdfReader(pdf_file, strict=False)
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        if len(text) >= max_chars:
                            break
                except Exception as pe:
                    logger.warning(f"Could not extract text from PDF page: {pe}")
        except Exception as e:
            logger.error(f"Error parsing PDF bytes: {str(e)}")
            return "[Note: Could not extract text from this PDF document. It may be an image-only scan or encrypted.]"
        return text if text.strip() else "[Note: No readable text found in this PDF document.]"


    @staticmethod
    def _extract_docx(file_bytes: bytes) -> str:
        try:
            docx_file = io.BytesIO(file_bytes)
            doc = docx.Document(docx_file)
            text = [para.text for para in doc.paragraphs]
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error parsing DOCX bytes: {str(e)}")
            raise ValueError(f"Failed to parse DOCX document: {str(e)}")

    @staticmethod
    def _extract_txt(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error parsing TXT bytes: {str(e)}")
            raise ValueError(f"Failed to parse TXT file: {str(e)}")

    @staticmethod
    def get_image_base64_payload(file_bytes: bytes) -> str:
        """
        Convert image bytes to a base64 encoded string.
        """
        try:
            return base64.b64encode(file_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            raise ValueError(f"Failed to process image: {str(e)}")
