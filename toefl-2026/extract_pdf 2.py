#!/usr/bin/env python3
import sys
import os
import Quartz
from Quartz import (
    CGPDFDocumentCreateWithURL,
    CFURLCreateWithFileSystemPath,
    kCFURLPOSIXPathStyle,
    CGPDFDocumentGetNumberOfPages,
    CGPDFDocumentGetPage,
    CGPDFPageGetBoxRect,
    kCGPDFMediaBox,
    CGContextDrawPDFPage,
    CGBitmapContextCreate,
    CGColorSpaceCreateDeviceRGB,
    kCGImageAlphaPremultipliedLast,
    kCGBitmapByteOrder32Big,
    CGContextSetRGBFillColor,
    CGContextFillRect,
    CGContextScaleCTM,
    CGBitmapContextCreateImage,
    CGImageDestinationCreateWithURL,
    CGImageDestinationAddImage,
    CGImageDestinationFinalize
)

def pdf_to_images(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_url = CFURLCreateWithFileSystemPath(None, pdf_path, kCFURLPOSIXPathStyle, False)
    pdf_doc = CGPDFDocumentCreateWithURL(pdf_url)
    
    if not pdf_doc:
        print(f"Error: Could not open PDF at {pdf_path}")
        return

    num_pages = CGPDFDocumentGetNumberOfPages(pdf_doc)
    print(f"Total pages: {num_pages}")

    for i in range(1, num_pages + 1):
        page = CGPDFDocumentGetPage(pdf_doc, i)
        if not page:
            continue
        
        rect = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)
        # rect is likely a CGRect object with origin and size
        width = int(rect.size.width * 2)
        height = int(rect.size.height * 2)
        
        color_space = CGColorSpaceCreateDeviceRGB()
        context = CGBitmapContextCreate(
            None, width, height, 8, width * 4, color_space,
            kCGImageAlphaPremultipliedLast | kCGBitmapByteOrder32Big
        )
        
        if not context:
            print(f"Error: Could not create context for page {i}")
            continue

        CGContextSetRGBFillColor(context, 1.0, 1.0, 1.0, 1.0)
        # Use rect from page to ensure correct dimensions
        CGContextFillRect(context, ((0, 0), (width, height)))
        CGContextScaleCTM(context, 2.0, 2.0)
        CGContextDrawPDFPage(context, page)
        
        image = CGBitmapContextCreateImage(context)
        
        output_file = os.path.join(output_dir, f"page_{i:03d}.png")
        output_url = CFURLCreateWithFileSystemPath(None, output_file, kCFURLPOSIXPathStyle, False)
        
        dest = CGImageDestinationCreateWithURL(output_url, "public.png", 1, None)
        CGImageDestinationAddImage(dest, image, None)
        CGImageDestinationFinalize(dest)
        
        print(f"Exported: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract_pdf.py <pdf_path> <output_dir>")
        sys.exit(1)
    
    pdf_to_images(sys.argv[1], sys.argv[2])
