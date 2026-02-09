import os
from fpdf import FPDF

def create_book(book_text, scene_paths, config):
    os.makedirs("exports/books", exist_ok=True)
    pdf_path = "exports/books/story.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for text, img in zip(book_text, scene_paths):
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.multi_cell(0, 10, text)
        pdf.image(img, x=10, y=50, w=180)

    pdf.output(pdf_path)
    return pdf_path
