from flask import Flask, request, send_file
from flask_cors import CORS
import os
import tempfile

# Latest Adobe SDK v4 Imports
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

app = Flask(__name__)
CORS(app)

# Keys Render ke Environment variables se fetch hongi
ADOBE_CLIENT_ID = os.environ.get("ADOBE_CLIENT_ID")
ADOBE_CLIENT_SECRET = os.environ.get("ADOBE_CLIENT_SECRET")

@app.route('/')
def home():
    return "Adobe PDF to Word API (v4) is running successfully!"

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
        # File server par save karein
        file.save(temp_pdf.name)

        # 1. Credentials setup
        credentials = ServicePrincipalCredentials(
            client_id=ADOBE_CLIENT_ID,
            client_secret=ADOBE_CLIENT_SECRET
        )
        pdf_services = PDFServices(credentials=credentials)

        # 2. PDF upload karein
        with open(temp_pdf.name, 'rb') as f:
            input_stream = f.read()
            
        input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)

        # 3. Export to DOCX ka naya Job create karein
        export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX)
        export_pdf_job = ExportPDFJob(input_asset=input_asset, export_pdf_params=export_pdf_params)

        # 4. Job submit karein aur process hone ka wait karein
        location = pdf_services.submit(export_pdf_job)
        pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)

        # 5. Output fetch karein aur local temporary file mein save karein
        result_asset = pdf_services_response.get_result().get_asset()
        stream_asset = pdf_services.get_content(result_asset)

        with open(temp_docx.name, "wb") as f:
            f.write(stream_asset.get_input_stream())

        return send_file(
            temp_docx.name,
            as_attachment=True,
            download_name=file.filename.replace('.pdf', '-editable.docx'),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return {"message": f"Adobe API Error: {str(e)}"}, 500
    finally:
        # Server memory clean up
        if os.path.exists(temp_pdf.name):
            os.unlink(temp_pdf.name)
        if os.path.exists(temp_docx.name):
            try:
                os.unlink(temp_docx.name)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
