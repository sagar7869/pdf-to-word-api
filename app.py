from flask import Flask, request, send_file
from flask_cors import CORS
import os
import tempfile
from adobe.pdfservices.operation.auth.credentials import Credentials
from adobe.pdfservices.operation.execution_context import ExecutionContext
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfops.export_pdf_operation import ExportPDFOperation
from adobe.pdfservices.operation.pdfops.options.exportpdf.export_pdf_target_format import ExportPDFTargetFormat

app = Flask(__name__)
CORS(app)

# Code ke andar key nahi daalenge, server se securely fetch karenge
ADOBE_CLIENT_ID = os.environ.get("ADOBE_CLIENT_ID")
ADOBE_CLIENT_SECRET = os.environ.get("ADOBE_CLIENT_SECRET")

@app.route('/')
def home():
    return "Adobe PDF to Word API is running successfully!"

@app.route('/convert/pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    if not ADOBE_CLIENT_ID or not ADOBE_CLIENT_SECRET:
        return {"message": "API keys are missing on the server!"}, 500

    if 'file' not in request.files:
        return {"message": "No file provided"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"message": "No selected file"}, 400

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    temp_pdf.close()
    temp_docx.close()

    try:
        file.save(temp_pdf.name)

        credentials = Credentials.service_principal_credentials_builder() \
            .with_client_id(ADOBE_CLIENT_ID) \
            .with_client_secret(ADOBE_CLIENT_SECRET) \
            .build()
        
        execution_context = ExecutionContext.create(credentials)
        export_pdf_operation = ExportPDFOperation.create_new(ExportPDFTargetFormat.DOCX)
        
        source_file_ref = FileRef.create_from_local_file(temp_pdf.name)
        export_pdf_operation.set_input(source_file_ref)
        
        result = export_pdf_operation.execute(execution_context)
        
        if os.path.exists(temp_docx.name):
            os.unlink(temp_docx.name)
        result.save_as(temp_docx.name)

        return send_file(
            temp_docx.name,
            as_attachment=True,
            download_name=file.filename.replace('.pdf', '-editable.docx'),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return {"message": f"Adobe API Error: {str(e)}"}, 500
    finally:
        if os.path.exists(temp_pdf.name):
            os.unlink(temp_pdf.name)
        if os.path.exists(temp_docx.name):
            try:
                os.unlink(temp_docx.name)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
