from flask import Flask, request, send_file, make_response
from PIL import Image
import io
import base64
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def make_collage(images, rows, cols, border_size=10, border_color=(255, 255, 255)):
    """Create collage with optional borders"""
    max_width = max(img.size[0] for img in images)
    max_height = max(img.size[1] for img in images)
    
    # Add borders to images
    bordered_images = []
    for img in images:
        new_img = Image.new('RGB', 
                          (max_width + 2*border_size, max_height + 2*border_size),
                          border_color)
        new_img.paste(img, (border_size, border_size))
        bordered_images.append(new_img)
    
    # Create canvas with spacing
    collage = Image.new('RGB', 
                       ((max_width + 2*border_size) * cols, 
                        (max_height + 2*border_size) * rows))
    
    # Paste images
    for index, img in enumerate(bordered_images[:rows*cols]):
        row = index // cols
        col = index % cols
        collage.paste(img, (col * (max_width + 2*border_size), 
                           row * (max_height + 2*border_size)))
    
    return collage

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def generate_html_response(collage=None, error=None, share_code=None, rows=None, cols=None, image_count=None):
    """Generate complete HTML response"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎨 Collage Maker Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }}
            .card {{
                border-radius: 10px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            }}
            .btn-primary {{
                background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
                border: none;
                font-weight: bold;
            }}
            .form-range::-webkit-slider-thumb {{
                background: #667eea;
            }}
            .collage-img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card p-4">
                        <h1 class="text-center mb-4">🎨 Collage Maker Pro</h1>
                        <p class="text-center mb-4">Create beautiful collages and share them with friends!</p>
    """

    if error:
        html += f"""
                        <div class="alert alert-warning">{error}</div>
        """

    if collage:
        html += f"""
                        <div class="text-center mb-4">
                            <img src="data:image/png;base64,{collage}" class="collage-img" alt="Your Collage">
                            <p class="mt-2">{rows}x{cols} Collage | {image_count} images</p>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-6 text-center">
                                <a href="/download" class="btn btn-primary btn-lg">Download Collage</a>
                            </div>
                            <div class="col-md-6">
                                <div class="card p-3">
                                    <h5>Share Your Creation</h5>
                                    <p>Share code: <code>{share_code}</code></p>
                                    <p>Give this code to friends to view your collage!</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="text-center mt-4">
                            <h4>Share on Social Media</h4>
                            <a href="#"><img src="https://img.icons8.com/color/48/000000/twitter.png" width="40"/></a>
                            <a href="#"><img src="https://img.icons8.com/color/48/000000/facebook-new.png" width="40"/></a>
                            <a href="#"><img src="https://img.icons8.com/color/48/000000/instagram-new.png" width="40"/></a>
                        </div>
        """
    else:
        html += """
                        <form method="POST" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="images" class="form-label">📤 Upload Images (JPG/PNG)</label>
                                <input class="form-control" type="file" id="images" name="images" multiple accept="image/jpeg,image/png">
                                <div class="form-text">Select multiple images for best results</div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label for="rows" class="form-label">Number of Rows</label>
                                    <input type="range" class="form-range" min="1" max="6" value="2" id="rows" name="rows" oninput="rowsValue.innerText = this.value">
                                    <div class="text-center" id="rowsValue">2</div>
                                </div>
                                <div class="col-md-6">
                                    <label for="cols" class="form-label">Number of Columns</label>
                                    <input type="range" class="form-range" min="1" max="6" value="2" id="cols" name="cols" oninput="colsValue.innerText = this.value">
                                    <div class="text-center" id="colsValue">2</div>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label for="border_size" class="form-label">Border Size (px)</label>
                                    <input type="range" class="form-range" min="0" max="30" value="10" id="border_size" name="border_size">
                                </div>
                                <div class="col-md-6">
                                    <label for="border_color" class="form-label">Border Color</label>
                                    <input type="color" class="form-control form-control-color" id="border_color" name="border_color" value="#FFFFFF" title="Choose border color">
                                </div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg">✨ Generate Collage</button>
                            </div>
                        </form>
                        
                        <div class="mt-4">
                            <h5>How to use:</h5>
                            <ol>
                                <li>Upload 2+ images</li>
                                <li>Choose layout</li>
                                <li>Generate & Share!</li>
                            </ol>
                        </div>
        """

    html += """
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        rows = int(request.form.get('rows', 2))
        cols = int(request.form.get('cols', 2))
        border_size = int(request.form.get('border_size', 10))
        border_color = request.form.get('border_color', '#FFFFFF')
        
        # Handle file uploads
        uploaded_files = request.files.getlist('images')
        if len(uploaded_files) < rows * cols:
            return generate_html_response(error=f"You need at least {rows*cols} images (uploaded: {len(uploaded_files)})")
        
        # Process images
        images = []
        for file in uploaded_files:
            if file.filename == '':
                continue
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            images.append(Image.open(filepath))
        
        # Create collage
        rgb_color = hex_to_rgb(border_color)
        collage = make_collage(images, rows, cols, border_size, rgb_color)
        
        # Save collage to bytes for display
        img_io = io.BytesIO()
        collage.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('ascii')
        
        # Generate share code
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        share_code = f"CM-{timestamp}-{rows}x{cols}"
        
        return generate_html_response(
            collage=img_base64,
            share_code=share_code,
            rows=rows,
            cols=cols,
            image_count=len(uploaded_files)
        )
    
    return generate_html_response()

@app.route('/download')
def download():
    # In a real app, you would get the collage from session or database
    # For this example, we'll create a simple placeholder
    img = Image.new('RGB', (800, 600), color='gray')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='collage.png')

if __name__ == '__main__':
    app.run(debug=True)
