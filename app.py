from flask import Flask, request, send_file
from PIL import Image
import io
import base64
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def image_to_base64(path):
    """Converts an image file to base64 for embedding in HTML."""
    with Image.open(path) as img:
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return base64.b64encode(img_io.read()).decode('utf-8')

def generate_html_response(error=None):
    """Generates the HTML page with upload form and image gallery."""
    html = """
    <html>
    <head><title>📸 Welcome to PhotoVault</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
    <div class="container py-4">
        <h1 class="text-center mb-4">📸 Welcome to PhotoVault</h1>
        <p class="text-center">What would you like to upload?</p>
    """

    if error:
        html += f"<div class='alert alert-danger'>{error}</div>"

    html += """
        <form method="POST" enctype="multipart/form-data" class="mb-4">
            <input type="file" name="images" accept="image/*" class="form-control mb-2" multiple>
            <button type="submit" class="btn btn-primary">Upload</button>
        </form>
        <form method="POST" action="/clear" class="mb-4">
            <button type="submit" class="btn btn-danger">Clear All Images</button>
        </form>
    """

    # Display all uploaded images
    html += "<div class='row'>"
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_data = image_to_base64(filepath)
            html += f"""
            <div class='col-md-4 mb-3'>
                <div class='card'>
                    <img src="data:image/png;base64,{img_data}" class='card-img-top' alt='{filename}'>
                    <div class='card-body text-center'>
                        <p class='card-text'>{filename}</p>
                    </div>
                </div>
            </div>
            """
    html += "</div></div></body></html>"
    return html

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('images')
        if not uploaded_files or all(file.filename == '' for file in uploaded_files):
            return generate_html_response(error="No images uploaded.")

        filenames = []
        for uploaded_file in uploaded_files:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)
            filenames.append(filename)

        # Generate a base64 preview for the uploaded images
        uploaded_images_base64 = []
        for filename in filenames:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img_data = image_to_base64(filepath)
            uploaded_images_base64.append(img_data)

        return generate_html_response(error=None)

    return generate_html_response()

@app.route('/clear', methods=['POST'])
def clear_images():
    """Clears all images from the upload folder."""
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            os.remove(filepath)  # Remove the image file
    return generate_html_response(error="All images have been cleared.")

if __name__ == '__main__':
    app.run(debug=True, port=5050)
