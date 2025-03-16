import os
import zipfile
import tempfile
import shutil
from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
import rarfile
from tqdm import tqdm
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加文件处理程序，确保日志也写入文件
try:
    file_handler = logging.FileHandler('cbz2pdf_conversion.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"无法设置日志文件: {e}")

class CBZtoPDFConverter:
    """
    A class to convert CBZ (Comic Book ZIP) files to PDF format.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.supported_image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        self.temp_dir = None
    
    def _create_temp_dir(self):
        """Create a temporary directory for extraction."""
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir
    
    def _clean_temp_dir(self):
        """Clean up the temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def _extract_cbz(self, cbz_path, extract_dir):
        """Extract the CBZ file to the specified directory."""
        try:
            with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
                # Get list of files in the archive
                file_list = [f for f in zip_ref.namelist() if not f.endswith('/')]
                total_files = len(file_list)
                
                # Extract all files
                for index, file in enumerate(file_list, 1):
                    logger.info(f"正在解压文件 {index}/{total_files}: {file}")
                    # 获取目标文件的完整路径
                    target_path = os.path.join(extract_dir, file)
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    # 解压文件
                    with zip_ref.open(file) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
            logger.info(f"Successfully extracted {cbz_path}")
            return True
        except Exception as e:
            logger.error(f"Error extracting CBZ file: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _extract_cbr(self, cbr_path, extract_dir):
        """Extract the CBR file to the specified directory."""
        try:
            with rarfile.RarFile(cbr_path, 'r') as rar_ref:
                # Get list of files in the archive
                file_list = [f for f in rar_ref.namelist() if not f.endswith('/')]
                total_files = len(file_list)
                
                # Extract all files
                for index, file in enumerate(file_list, 1):
                    logger.info(f"正在解压文件 {index}/{total_files}: {file}")
                    # 获取目标文件的完整路径
                    target_path = os.path.join(extract_dir, file)
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    # 解压文件
                    with rar_ref.open(file) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
            logger.info(f"Successfully extracted {cbr_path}")
            return True
        except Exception as e:
            logger.error(f"Error extracting CBR file: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _get_sorted_image_files(self, directory):
        """Get a sorted list of image files from the directory."""
        image_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext in self.supported_image_extensions:
                    image_files.append(file_path)
        
        # Sort files naturally (1, 2, 10 instead of 1, 10, 2)
        return sorted(image_files, key=self._natural_sort_key)
    
    def _natural_sort_key(self, s):
        """
        Return a key for natural sorting.
        For example, ['1', '10', '2'] will be sorted as ['1', '2', '10'].
        """
        import re
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', os.path.basename(s))]
    
    def _create_pdf(self, image_files, output_pdf_path):
        """Create a PDF from the list of image files."""
        try:
            logger.info(f"开始创建PDF，共 {len(image_files)} 张图片")
            pdf_writer = PdfWriter()
            processed_images = 0
            total_images = len(image_files)
            
            for index, img_path in enumerate(image_files, 1):
                try:
                    logger.info(f"正在处理图片 {index}/{total_images}: {img_path}")
                    img = Image.open(img_path)
                    
                    # Convert to RGB if the image is in RGBA mode
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    elif img.mode != 'RGB':
                        logger.debug(f"转换图片模式从 {img.mode} 到 RGB")
                        img = img.convert('RGB')
                    
                    # Create a temporary file for the PDF page
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                        temp_pdf_path = temp_pdf.name
                    
                    logger.debug(f"保存图片到临时PDF: {temp_pdf_path}")
                    img.save(temp_pdf_path, 'PDF', resolution=100.0)
                    
                    # Add the page to the PDF writer using PdfReader
                    logger.debug(f"读取临时PDF并添加页面")
                    try:
                        pdf_reader = PdfReader(temp_pdf_path)
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)
                        processed_images += 1
                    except Exception as reader_error:
                        logger.error(f"读取PDF页面时出错: {reader_error}")
                        logger.error(traceback.format_exc())
                    
                    # Remove the temporary PDF file
                    try:
                        os.unlink(temp_pdf_path)
                        logger.debug(f"删除临时PDF文件: {temp_pdf_path}")
                    except Exception as unlink_error:
                        logger.warning(f"无法删除临时文件 {temp_pdf_path}: {unlink_error}")
                    
                except Exception as e:
                    logger.error(f"处理图片时出错 {img_path}: {e}")
                    logger.error(traceback.format_exc())
            
            logger.info(f"成功处理了 {processed_images}/{len(image_files)} 张图片")
            
            if processed_images == 0:
                logger.error("没有成功处理任何图片，无法创建PDF")
                return False
            
            # Write the final PDF
            try:
                logger.info(f"写入最终PDF到: {output_pdf_path}")
                with open(output_pdf_path, 'wb') as f:
                    pdf_writer.write(f)
                
                # 验证PDF文件是否已创建且大小大于0
                if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
                    logger.info(f"成功创建PDF，文件大小: {os.path.getsize(output_pdf_path)} 字节")
                    return True
                else:
                    logger.error(f"PDF文件创建失败或大小为0: {output_pdf_path}")
                    return False
            except Exception as write_error:
                logger.error(f"写入PDF文件时出错: {write_error}")
                logger.error(traceback.format_exc())
                return False
        except Exception as e:
            logger.error(f"创建PDF时出错: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def convert(self, input_path, output_path=None):
        """
        Convert a CBZ file to PDF.
        
        Args:
            input_path (str): Path to the CBZ file.
            output_path (str, optional): Path for the output PDF file.
                If not provided, it will use the same name as the input file with .pdf extension.
        
        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        logger.info(f"开始转换: {input_path}")
        
        if not os.path.exists(input_path):
            logger.error(f"输入文件不存在: {input_path}")
            return False
        
        # Determine file type
        file_ext = os.path.splitext(input_path)[1].lower()
        logger.info(f"文件类型: {file_ext}")
        
        # Set default output path if not provided
        if not output_path:
            output_path = os.path.splitext(input_path)[0] + '.pdf'
        
        logger.info(f"输出路径: {output_path}")
        
        try:
            # Create temporary directory
            extract_dir = self._create_temp_dir()
            logger.info(f"创建临时目录: {extract_dir}")
            
            # Extract the archive based on file type
            extraction_success = False
            if file_ext == '.cbz':
                logger.info("开始解压CBZ文件")
                extraction_success = self._extract_cbz(input_path, extract_dir)
            elif file_ext == '.cbr':
                logger.info("开始解压CBR文件")
                extraction_success = self._extract_cbr(input_path, extract_dir)
            else:
                logger.error(f"不支持的文件格式: {file_ext}")
                self._clean_temp_dir()
                return False
            
            if not extraction_success:
                logger.error("解压失败")
                self._clean_temp_dir()
                return False
            
            # Get sorted image files
            logger.info("获取并排序图片文件")
            image_files = self._get_sorted_image_files(extract_dir)
            logger.info(f"找到 {len(image_files)} 个图片文件")
            
            if not image_files:
                logger.error("在压缩包中没有找到图片文件")
                self._clean_temp_dir()
                return False
            
            # Create PDF
            logger.info("开始创建PDF")
            pdf_success = self._create_pdf(image_files, output_path)
            
            # Clean up
            logger.info("清理临时文件")
            self._clean_temp_dir()
            
            if pdf_success:
                logger.info("转换成功完成")
            else:
                logger.error("PDF创建失败")
            
            return pdf_success
        
        except Exception as e:
            logger.error(f"转换过程中出错: {e}")
            logger.error(traceback.format_exc())
            self._clean_temp_dir()
            return False

# Function for batch conversion
def batch_convert(input_files, output_dir=None):
    """
    Convert multiple CBZ files to PDF.
    
    Args:
        input_files (list): List of paths to CBZ files.
        output_dir (str, optional): Directory for output PDF files.
            If not provided, PDFs will be created in the same directory as input files.
    
    Returns:
        dict: Dictionary with input file paths as keys and conversion status as values.
    """
    converter = CBZtoPDFConverter()
    results = {}
    
    for input_file in input_files:
        if output_dir:
            output_file = os.path.join(output_dir, os.path.basename(os.path.splitext(input_file)[0]) + '.pdf')
        else:
            output_file = os.path.splitext(input_file)[0] + '.pdf'
        
        logger.info(f"Converting {input_file} to {output_file}")
        success = converter.convert(input_file, output_file)
        results[input_file] = success
    
    return results 