import gradio as gr
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw
import tempfile
import requests
from io import BytesIO

# GitHub repository base URL for loading images
GITHUB_REPO_URL = "https://raw.githubusercontent.com/kalanpeace/Caeliai-Genesis-01-Vision-Benchmark/main/"

# Custom CSS for dark theme with exact color specifications
custom_css = """
/* Main background */
.gradio-container {
    background-color: #121212 !important;
    color: #F5F5F5 !important;
}

/* Content cards */
.gradio-group {
    background-color: #1E1E1E !important;
    border-radius: 15px !important;
    border: 1px solid #4A90E2 !important;
    padding: 20px !important;
    margin: 15px 0 !important;
}

/* Typography */
.gradio-group h1, .gradio-group h2, .gradio-group h3 {
    color: #F5F5F5 !important;
    margin-bottom: 10px !important;
}

.gradio-group h1 {
    font-size: 24px !important;
    font-weight: bold !important;
}

.gradio-group h2 {
    font-size: 20px !important;
    font-weight: 600 !important;
}

.gradio-group h3 {
    font-size: 16px !important;
    font-weight: 500 !important;
}

.gradio-group p {
    color: #AAAAAA !important;
    line-height: 1.6 !important;
    margin-bottom: 15px !important;
}

/* Dropdown styling */
.gradio-dropdown {
    background-color: #1E1E1E !important;
    border: 1px solid #4A90E2 !important;
    border-radius: 8px !important;
    color: #F5F5F5 !important;
}

/* Image and gallery styling */
.gradio-image, .gradio-gallery {
    background-color: transparent !important;
    border: none !important;
}

.gradio-gallery .thumbnail {
    border-radius: 8px !important;
}

/* Gallery captions */
.gradio-gallery .caption {
    font-size: 0.8rem !important;
    color: #AAAAAA !important;
    text-align: center !important;
    margin-top: 5px !important;
}

/* Button styling */
.gradio-button {
    background-color: #4A90E2 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #F5F5F5 !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
}

.gradio-button:hover {
    background-color: #5BA0F2 !important;
}

/* Text inputs and textareas */
.gradio-textbox, .gradio-textarea {
    background-color: #1E1E1E !important;
    border: 1px solid #4A90E2 !important;
    border-radius: 8px !important;
    color: #F5F5F5 !important;
}

/* Main header styling */
.main-header {
    background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%) !important;
    border: 1px solid #4A90E2 !important;
    border-radius: 15px !important;
    padding: 25px !important;
    margin-bottom: 25px !important;
    text-align: center !important;
}

.main-header h1 {
    color: #F5F5F5 !important;
    font-size: 28px !important;
    font-weight: bold !important;
    margin: 0 !important;
}

.main-header p {
    color: #AAAAAA !important;
    font-size: 16px !important;
    margin: 10px 0 0 0 !important;
}

/* Test section headers */
.test-header {
    border-bottom: 2px solid #4A90E2 !important;
    padding-bottom: 10px !important;
    margin-bottom: 20px !important;
}

.test-emoji {
    font-size: 24px !important;
    margin-right: 10px !important;
}

/* Success/failure indicators */
.success-border {
    border: 3px solid #28A745 !important;
}

.failure-border {
    border: 3px solid #DC3545 !important;
}
"""

# Mock data structure based on the provided mapping
MOCK_RESULTS = {
}

def add_border(image_source, color):
    """Add a colored border to an image using Pillow library."""
    try:
        # Check if image_source is a URL or local path
        if image_source.startswith(('http://', 'https://')):
            # Fetch the image from URL
            response = requests.get(image_source, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            # Local file path
            if not os.path.exists(image_source):
                return get_placeholder_path()
            img = Image.open(image_source)
        
        # Create a new image with border
        border_width = 4
        new_width = img.width + 2 * border_width
        new_height = img.height + 2 * border_width
        
        # Create new image with border color
        bordered_img = Image.new('RGB', (new_width, new_height), color)
        
        # Paste original image in center
        bordered_img.paste(img, (border_width, border_width))
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        bordered_img.save(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error adding border to {image_source}: {e}")
        return get_placeholder_path()

def get_placeholder_path():
    """Return path to placeholder image."""
    placeholder_path = "assets/placeholder.png"
    if not os.path.exists(placeholder_path):
        # Create a simple placeholder if it doesn't exist
        os.makedirs("assets", exist_ok=True)
        img = Image.new('RGB', (200, 200), '#2A2A2A')
        draw = ImageDraw.Draw(img)
        try:
            # Try to get a font, fall back to default if not available
            from PIL import ImageFont
            font = ImageFont.load_default()
            draw.text((60, 95), "No Image", fill='#AAAAAA', font=font)
        except:
            draw.text((60, 95), "No Image", fill='#AAAAAA')
        img.save(placeholder_path)
    return placeholder_path

def create_gallery_data(images, test_type="impostor"):
    """Create gallery data with enhanced captions based on test type."""
    gallery_data = []
    
    for img_data in images:
        # Determine border color based on correctness
        border_color = "#28A745" if img_data['correct'] else "#DC3545"
        
        # Get image URL from GitHub repository
        image_relative_path = img_data.get('image_path', 'images/placeholder.png')
        image_url = GITHUB_REPO_URL + image_relative_path
        
        # Add border
        bordered_path = add_border(image_url, border_color)
        
        # Create enhanced caption based on test type
        filename = img_data['filename']
        confidence = img_data['confidence']
        is_correct = img_data['correct']
        
        if test_type == "impostor":
            # Extract brand from filename for impostor test
            if "rick" in filename.lower():
                brand = "Rick Owens"
            elif "yohji" in filename.lower() or "yamamoto" in filename.lower():
                brand = "Yohji Yamamoto"
            elif "ann" in filename.lower():
                brand = "Ann Demeulemeester"
            else:
                brand = "Rick Owens"  # Default
            
            status = "✅" if is_correct else "❌"
            caption = f"{status} {brand} | Conf: {confidence:.3f}"
            
        elif test_type == "family":
            # Extract collection info for family test
            if "spring_2010" in filename.lower():
                collection = "Spring 2010"
            elif "fall_2016" in filename.lower():
                collection = "Fall 2016"
            elif "spring_2006" in filename.lower():
                collection = "Spring 2006"
            elif "fall_2003" in filename.lower():
                collection = "Fall 2003"
            else:
                collection = "Spring 2010"  # Default
            
            status = "✅" if is_correct else "❌"
            caption = f"{status} {collection} | Conf: {confidence:.3f}"
            
        elif test_type == "needle":
            # Simple target vs impostor for needle test
            if "target" in filename.lower() or confidence > 0.95:
                label = "🎯 TARGET"
            else:
                label = "Impostor"
            
            caption = f"{label} | Conf: {confidence:.3f}"
            
        else:
            # Fallback to original format
            caption = f"{filename}\nConfidence: {confidence:.3f}"
        
        gallery_data.append((bordered_path, caption))
    
    return gallery_data

def update_ui_for_model(model_name):
    """Update the UI based on selected model."""
    results = MOCK_RESULTS[model_name]
    
    # Get target image URL for family test
    target_image_relative_path = results['family_test'].get('target_image_path', 'images/placeholder.png')
    target_image_url = GITHUB_REPO_URL + target_image_relative_path
    
    # Create gallery data for each test with appropriate type
    impostor_gallery = create_gallery_data(results['impostor_test']['sample_images'], "impostor")
    family_gallery = create_gallery_data(results['family_test']['sample_results'], "family")
    needle_gallery = create_gallery_data(results['needle_test']['sample_images'], "needle")
    
    # Create statistics
    # Calculate clarity for impostor test
    successful_uncertainty = results['impostor_test']['total_tests'] - results['impostor_test']['uncertain']
    flawed_uncertainty = results['impostor_test']['uncertain']
    
    impostor_stats = f"""
**Results Summary:** {results['impostor_test']['total_tests']} Tests searching through **12,147 Rick Owens images** | **{successful_uncertainty}** Successful Uncertainty Checks | **{flawed_uncertainty}** Flawed Uncertainty Checks
    """
    
    # Calculate clarity for family test
    weak_cohesion = results['family_test']['total_collections'] - results['family_test']['strong_recognition']
    
    family_stats = f"""
**Results Summary:** {results['family_test']['total_collections']} Collections Tested from **12,195 total images** | **{results['family_test']['strong_recognition']}** with Strong Cohesion | **{weak_cohesion}** with Weak Cohesion
    """
    
    # Calculate clarity for needle test
    failures = results['needle_test']['total_searches'] - results['needle_test']['perfect_match']
    
    needle_stats = f"""
**Results Summary:** {results['needle_test']['total_searches']} Searches through **12,195 total images** | **{results['needle_test']['perfect_match']}** Perfect Matches | **{failures}** Failures
    """
    
    return (
        target_image_url,
        impostor_gallery,
        family_gallery, 
        needle_gallery,
        impostor_stats,
        family_stats,
        needle_stats
    )

def create_interface():
    """Create the main Gradio interface."""
    
    with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as demo:
        
        # Header
        gr.HTML("""
        <div class="main-header">
            <h1>Caeliai Genesis 01: The Vision Benchmark</h1>
            <p>Comprehensive analysis of vision models on Rick Owens fashion recognition tasks</p>
            <p style="font-size: 14px; margin-top: 15px; color: #4A90E2;">Foundational research exploring computational approaches to fashion and aesthetic understanding</p>
        </div>
        """)
        
        # Model selector
        with gr.Row():
            model_dropdown = gr.Dropdown(
                choices=["CLIP", "SigLIP", "DINOv2"],
                value="DINOv2",
                label="Select AI Model",
                info="Choose which model's test results to display"
            )
        
        # Test 1: Impostor Test
        with gr.Group():
            gr.Markdown("""
            <div class="test-header">
                <h2>Test 1: The Impostor Test</h2>
                <h3 style="color: #4A90E2;">Brand vs. Brand Discrimination</h3>
            </div>
            
            **Challenge:** Can the model spot a true Rick Owens piece among convincing "impostor" looks from other designers?
            
            **Why it's difficult:** Models only see pixels, not brand heritage. This tests if they can learn the subtle, unique "handwriting" of a designer, even when another designer's work looks very similar.
            
            **How it works:**
            1. Model sees a Rick Owens image (query)
            2. It must find other Rick Owens pieces from a pool contaminated with "impostor" looks from other designers
            3. Model **FAILS** if it thinks an impostor is more similar than a real Rick Owens piece (a negative "noise gap")
            """)
            
            impostor_stats_display = gr.Markdown()
            impostor_gallery = gr.Gallery(
                label="Test Results (Green = Success, Red = Failure)",
                show_label=True,
                elem_id="impostor_gallery",
                columns=7,
                rows=1,
                height="auto"
            )
        
        # Test 2: Family Resemblance Test
        with gr.Group():
            gr.Markdown("""
            <div class="test-header">
                <h2>Test 2: The Family Resemblance Test</h2>
                <h3 style="color: #4A90E2;">Collection Cohesion</h3>
            </div>
            
            **Challenge:** Does the model understand that looks from the same collection are part of a "family," even if they look very different?
            
            **Why it's difficult:** A single collection contains diverse pieces. The model must understand the core theme or mood, not just match colors or shapes.
            
            **How it works:**
            1. Model sees a Rick Owens Spring 2010 piece (query image)
            2. Model must find OTHER Rick Owens Spring 2010 pieces
            3. Model gets it WRONG when it picks Rick Owens Fall 2016, Spring 2006, Fall 2003, etc.
            4. The challenge: What makes Spring 2010 different from Fall 2016, even though both are Rick Owens?
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("**Query Image:**")
                    target_image = gr.Image(
                        label="Target Collection",
                        show_label=False,
                        height=200,
                        width=200
                    )
                
                with gr.Column(scale=3):
                    family_stats_display = gr.Markdown()
                    family_gallery = gr.Gallery(
                        label="Collection Results (Green = Same Collection, Red = Wrong Collection)",
                        show_label=True,
                        elem_id="family_gallery",
                        columns=7,
                        rows=1,
                        height="auto"
                    )
        
        # Test 3: Needle in a Haystack Test
        with gr.Group():
            gr.Markdown("""
            <div class="test-header">
                <h2>Test 3: The Needle in a Haystack Test</h2>
                <h3 style="color: #4A90E2;">Exact Match Precision</h3>
            </div>
            
            **Challenge:** Can the model find the one identical image in a pile of extremely similar looks from the same show?
            
            **Why it's difficult:** This is a test of pure precision. The "haystack" is filled with items from the exact same collection, making the true duplicate incredibly difficult to spot.
            
            **How it works:**
            1. Model receives one target image from a specific collection
            2. It must find the EXACT SAME image hidden among 30+ very similar pieces from the same collection
            3. Model **FAILS** if it picks a similar-but-different piece instead of the exact duplicate
            4. The challenge: Spotting identical fabric patterns, poses, and details with pixel-perfect precision
            """)
            
            needle_stats_display = gr.Markdown()
            needle_gallery = gr.Gallery(
                label="Search Results (Green = Perfect Match, Red = Wrong Match)",
                show_label=True,
                elem_id="needle_gallery",
                columns=7,
                rows=1,
                height="auto"
            )
        
        # Update function
        model_dropdown.change(
            fn=update_ui_for_model,
            inputs=[model_dropdown],
            outputs=[
                target_image,
                impostor_gallery,
                family_gallery,
                needle_gallery,
                impostor_stats_display,
                family_stats_display,
                needle_stats_display
            ]
        )
        
        # Initialize with default model
        demo.load(
            fn=update_ui_for_model,
            inputs=[model_dropdown],
            outputs=[
                target_image,
                impostor_gallery,
                family_gallery,
                needle_gallery,
                impostor_stats_display,
                family_stats_display,
                needle_stats_display
            ]
        )
        
        # Call to Action Section
        gr.HTML("""
        <div style="margin-top: 40px; padding: 30px; background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%); border: 1px solid #4A90E2; border-radius: 15px; text-align: center;">
            <hr style="border: none; height: 2px; background: #4A90E2; margin: 0 0 25px 0;">
            <h3 style="color: #F5F5F5; font-size: 24px; margin-bottom: 15px;">Foundational Research</h3>
            <p style="color: #AAAAAA; font-size: 16px; line-height: 1.6; margin-bottom: 25px;">
                This benchmark represents foundational research into computational understanding of fashion and aesthetic principles. 
                Our investigation continues into the fundamental challenges of visual understanding in complex design domains.
            </p>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                <a href="https://github.com/kalanpeace/Caeliai" target="_blank" style="
                    display: inline-block; 
                    padding: 12px 24px; 
                    background: #4A90E2; 
                    color: #F5F5F5; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    font-weight: 500;
                    transition: background 0.3s ease;
                ">
                    ➡️ Follow our research on GitHub
                </a>
                <a href="docs/vision_benchmark_report.ipynb" target="_blank" style="
                    display: inline-block; 
                    padding: 12px 24px; 
                    background: transparent; 
                    color: #4A90E2; 
                    text-decoration: none; 
                    border: 1px solid #4A90E2; 
                    border-radius: 8px; 
                    font-weight: 500;
                    transition: all 0.3s ease;
                ">
                    ➡️ Read the technical report
                </a>
            </div>
        </div>
        """)
    
    return demo

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        debug=True
    ) 