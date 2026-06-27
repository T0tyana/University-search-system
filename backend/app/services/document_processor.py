import os
import logging
import pdfplumber
from docx import Document
from app.core.config import settings

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> list[tuple[str, int]]:
    """
    Извлекает текст из PDF файла постранично.
    
    Args:
        file_path: Путь к файлу PDF.
        
    Returns:
        Список кортежей (текст_страницы, номер_страницы).
        
    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если произошла ошибка парсинга.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    pages_data = []
    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                logger.warning(f"PDF file is empty: {file_path}")
                return []
            
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        clean_text = " ".join(page_text.split())
                        if clean_text:
                            pages_data.append((clean_text, i))
                except Exception as e:
                    logger.warning(f"Error extracting text from page {i}: {e}")
                    continue
                    
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}", exc_info=True)
        raise ValueError(f"Ошибка парсинга PDF файла: {str(e)}")
    
    return pages_data


def extract_text_from_docx(file_path: str) -> list[tuple[str, int]]:
    """
    Извлекает текст из DOCX файла.
    
    Args:
        file_path: Путь к файлу DOCX.
        
    Returns:
        Список кортежей (весь_текст, 1).
        
    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если произошла ошибка парсинга.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    try:
        doc = Document(file_path)
        full_text = [para.text for para in doc.paragraphs if para.text.strip()]
        text = '\n'.join(full_text)
        
        if not text.strip():
            logger.warning(f"DOCX file is empty: {file_path}")
            return []
            
        return [(text, 1)]
        
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}", exc_info=True)
        raise ValueError(f"Ошибка парсинга DOCX файла: {str(e)}")


def split_text_into_chunks(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Разбивает текст на чанки заданного размера с перекрытием.
    
    Args:
        text: Исходный текст.
        chunk_size: Размер чанка в символах.
        overlap: Количество символов перекрытия.
        
    Returns:
        Список текстовых чанков.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    
    # Валидация параметров
    if chunk_size <= 0:
        raise ValueError("Размер чанка должен быть больше 0")
    if overlap < 0:
        raise ValueError("Перекрытие не может быть отрицательным")
    if overlap >= chunk_size:
        raise ValueError("Перекрытие должно быть меньше размера чанка")
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += (chunk_size - overlap)
    
    return chunks


def process_document(file_id: str, file_ext: str) -> list[dict]:
    """
    Основной процессор документа: извлечение, очистка и чанкинг.
    
    Args:
        file_id: UUID файла.
        file_ext: Расширение файла (pdf/docx).
        
    Returns:
        Список словарей с ключами 'text' и 'page_number'.
        
    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если формат не поддерживается или произошла ошибка обработки.
    """
    upload_dir = "uploads"
    file_path = os.path.join(upload_dir, f"{file_id}.{file_ext}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_id}.{file_ext}")
    
    # Валидация расширения
    if file_ext not in {"pdf", "docx"}:
        raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")
    
    pages_data = []
    if file_ext == "pdf":
        pages_data = extract_text_from_pdf(file_path)
    elif file_ext == "docx":
        pages_data = extract_text_from_docx(file_path)
    
    if not pages_data:
        logger.warning(f"No text extracted from file: {file_id}.{file_ext}")
        return []
    
    final_chunks = []
    for page_text, page_num in pages_data:
        try:
            page_chunks = split_text_into_chunks(page_text)
            for chunk_text in page_chunks:
                final_chunks.append({
                    "text": chunk_text,
                    "page_number": page_num
                })
        except ValueError as e:
            logger.error(f"Error splitting text on page {page_num}: {e}")
            continue
    
    logger.info(f"Processed {len(final_chunks)} chunks from {len(pages_data)} pages")
    return final_chunks