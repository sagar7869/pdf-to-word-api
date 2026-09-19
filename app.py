from flask import Flask, request, send_file
from flask_cors import CORS
from pdf2docx import Converter
import os
import tempfile

app = Flask(__name__)
# CORS allow karta hai ki aapka frontend (GitHub Pages) is backend se communicate kar sake
CORS(app)

@app.route('/')
def home():
    return "PDF to Word API is running successfully!"

@app.route('/convert/pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    if 'file' not in request.files:
        return {"message": "No file provided"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"message": "No selected file"}, 400

    # Temporary files create karna conversion ke liye
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")

    try:
        # User ki aayi hui PDF save karna
        file.save(temp_pdf.name)

        # pdf2docx ka use karke 100% same layout aur formatting ke sath convert karna
        cv = Converter(temp_pdf.name)
        cv.convert(temp_docx.name, start=0, end=None)
        cv.close()

        # Converted Word file wapas frontend ko bhejna
        return send_file(
            temp_docx.name,
            as_attachment=True,
            download_name=file.filename.replace('.pdf', '-editable.docx'),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return {"message": str(e)}, 500
    finally:
        # Server ka space free karne ke liye temporary file delete karna
        if os.path.exists(temp_pdf.name):
            os.unlink(temp_pdf.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
