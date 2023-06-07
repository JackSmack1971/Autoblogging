import os
import openai
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import logging 

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY') 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

# Function to generate a clickable title using GPT-4
def generate_clickable_title(title):
    logger.info("Generating clickable title...")
    prompt = f"Generate a catchy and clickable title for a blog post based on the YouTube video titled '{title} Maximum 50 characters'."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    clickable_title = response['choices'][0]['message']['content'].strip()
    clickable_title = clickable_title.replace('"', '')  # Remove double quotes
    logger.info("Clickable title generated...")
    return clickable_title 

# Function to generate blog post using GPT-4
def generate_blog_post(row):
    logger.info("Generating blog post...")
    original_title = row['youtube video title']
    body = row['body description']
    asin = row['ASIN'] 

    # Generate a clickable title
    title = generate_clickable_title(original_title) 

    # Prepare a prompt for GPT-4
    prompt = f'Write 1200 words of content, without considering the links, Write ONLY in HTML. Consider SEO ranking factors, so use as much HTML as possible. Unordered lists, ordered lists, bold, italics, quotes, underlines. Do not include links to the Amazon products unless it\'s a referral link. Never mention the ASIN except in the links. This is a blog post about a YouTube video originally titled "{original_title}" do not mention the YouTube video, or the host of the video, just use the information, with the following description: "{body}". The associated product\'s ASIN is "{asin}". Please write a blog post about this. When you mention a brand, please add the following link <center><iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=incomestre0d3-20&language=en_US&marketplace=amazon&region=US&placement={asin}&asins={asin}&linkId=ea5840420af22ff2e663be3eee42c688&show_border=true&link_opens_in_new_window=true"></iframe></center>Replace B07S9H1VRC with the ASIN of the product associated with that {asin}' 

    # Generate the blog post using GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a WordPress Writer. You write articles with introductions, brands, and conclusions, each section should have some content. Under each product name you ALWAYS put an embedded iframe link. You only write in HTML, including headings, subheadings, etc. You also always embed Amazon iframe links after every mention of the brand."}, {"role": "user", "content": prompt} ] )
blog_post = response['choices'][0]['message']['content'].strip()
logger.info("Blog post generated...")
return title, blog_post 

# Function to upload post to WordPress 

def upload_to_wordpress(title, content): logger.info("Uploading post to WordPress...") url = os.getenv('WORDPRESS_API_URL') headers = { "Authorization": f"Bearer {os.getenv('WORDPRESS_AUTH_TOKEN')}", } data = { "title": title, "content": content, "status": "publish", } response = requests.post(url, headers=headers, json=data) logger.info("Post uploaded to WordPress...") return response.json() 

# Function to generate image using DALL-E 

def generate_image(prompt): logger.info("Generating image using DALL-E...") response = openai.Image.create( prompt=prompt, n=1, size="512x512" ) image_url = response['data'][0]['url'] logger.info("Image generated...") return image_url 

# Function to download and save image 

def save_image(image_url, filename): logger.info("Saving image...") response = requests.get(image_url) image = Image.open(BytesIO(response.content)) image.save(filename) logger.info("Image saved...") 

# Function to upload image to WordPress 

def upload_image_to_wordpress(filename): url = os.getenv('WORDPRESS_IMAGE_API_URL') headers = { "Authorization": f"Bearer {os.getenv('WORDPRESS_AUTH_TOKEN')}", "Content-Disposition": f"attachment; filename={filename}", "Content-Type": "image/jpeg", } with open(filename, "rb") as image_file: response = requests.post(url, headers=headers, data=image_file) return response.json() 

def main(): # Load CSV logger.info("Loading CSV...") df = pd.read_csv('file.csv') 

# Select the first row
first_row = df.iloc[0] 

# Generate blog post for the first row
logger.info("Generating blog post...")
title, blog_content = generate_blog_post(first_row)
logger.info("Blog post generated...") 

# Generate image using DALL-E
logger.info("Generating image...")
image_prompt = "A patterned repeated background image-only with coffee"  # Replace this with the appropriate prompt for your blog post
image_url = generate_image(image_prompt) 

# Save the generated image to your local system
logger.info("Saving image...")
filename = "generated_image.jpg"
save_image(image_url, filename)
logger.info("Image saved...") 

# Upload the image to WordPress
logger.info("Uploading image to WordPress...")
uploaded_image = upload_image_to_wordpress(filename)
logger.info(f"Uploaded image: {uploaded_image}")
logger.info("Image uploaded to WordPress...") 

# Add the uploaded image URL to the blog post content
image_url = uploaded_image['source_url']
blog_content_with_image = f'<img src="{image_url}" style="max-width:100%;height:auto;" alt="{image_prompt}"><br>{blog_content}' 

# Upload the blog post with the image
logger.info("Uploading post to WordPress...")
upload_to_wordpress(title, blog_content_with_image)
logger.info("Post uploaded to WordPress...") 

if name == "main": main()
