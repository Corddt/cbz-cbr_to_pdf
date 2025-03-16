#!/usr/bin/env python
"""
测试脚本，用于验证CBZ到PDF转换功能是否正常工作。
使用方法：python test_converter.py <cbz_file_path>
"""

import os
import sys
import logging
import traceback
from python_app.converter import CBZtoPDFConverter

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_conversion(input_file, output_file=None):
    """
    测试CBZ到PDF的转换功能。
    
    Args:
        input_file (str): 输入CBZ文件的路径
        output_file (str, optional): 输出PDF文件的路径
    
    Returns:
        bool: 转换是否成功
    """
    logger.info(f"开始测试转换: {input_file}")
    
    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return False
    
    # 如果未指定输出文件，则使用与输入文件相同的名称但扩展名为.pdf
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + '.pdf'
    
    logger.info(f"输出文件: {output_file}")
    
    try:
        # 创建转换器实例
        converter = CBZtoPDFConverter()
        
        # 执行转换
        success = converter.convert(input_file, output_file)
        
        if success:
            logger.info(f"转换成功! PDF文件已保存到: {output_file}")
            
            # 验证输出文件是否存在且大小大于0
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"PDF文件验证成功，大小: {os.path.getsize(output_file)} 字节")
                return True
            else:
                logger.error(f"PDF文件验证失败: 文件不存在或大小为0")
                return False
        else:
            logger.error("转换失败")
            return False
    
    except Exception as e:
        logger.error(f"转换过程中出错: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_converter.py <cbz_file_path> [output_pdf_path]")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = test_conversion(input_file, output_file)
    
    if success:
        print("测试成功!")
        return 0
    else:
        print("测试失败，请查看日志文件了解详情。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 