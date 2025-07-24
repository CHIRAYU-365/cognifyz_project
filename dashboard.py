import os
import sys
import time
import json
import re
import random
import io
from collections import Counter
from datetime import datetime

# Flask and web-related imports
from flask import Flask, request, render_template_string, session, send_from_directory, url_for, redirect
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Selenium for Web Scraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'cognifyz_final_project_secret_key'

# Define base directories for file storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SCREENSHOT_FOLDER = os.path.join(BASE_DIR, 'screenshots')
SCRAPED_DATA_FOLDER = os.path.join(BASE_DIR, 'scraped_data')

# Create necessary directories on startup
for folder in [UPLOAD_FOLDER, SCREENSHOT_FOLDER, SCRAPED_DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# --- UI Components (CSS, JS, HTML) ---
BASE_CSS = """
<style>
    :root {
        --bg-color: #f4f7f6; --card-color: #ffffff; --font-color: #333333;
        --primary-color: #007BFF; --primary-hover: #0056b3; --border-color: #dee2e6;
        --input-bg: #ffffff; --shadow-color: rgba(0, 0, 0, 0.08);
        --switch-bg: #ccc; --switch-slider: white;
        --alert-warn-bg: #fff3cd; --alert-warn-text: #856404; --alert-warn-border: #ffeeba;
    }
    body.dark-mode {
        --bg-color: #121212; --card-color: #1e1e1e; --font-color: #e0e0e0;
        --primary-color: #009DFF; --primary-hover: #007BFF; --border-color: #444444;
        --input-bg: #333333; --shadow-color: rgba(0, 0, 0, 0.4);
        --switch-bg: #555; --switch-slider: #121212;
        --alert-warn-bg: #332701; --alert-warn-text: #ffeeba; --alert-warn-border: #856404;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background-color: var(--bg-color); color: var(--font-color); margin: 0;
        padding: 0; transition: background-color 0.3s, color 0.3s; line-height: 1.6;
    }
    .container { max-width: 800px; margin: 2rem auto; padding: 0 2rem; }
    header {
        background-color: var(--card-color); padding: 1rem 2rem;
        border-bottom: 1px solid var(--border-color); box-shadow: 0 2px 4px var(--shadow-color);
        display: flex; justify-content: space-between; align-items: center;
        transition: background-color 0.3s, border-bottom 0.3s;
    }
    header h1 a { color: var(--primary-color); text-decoration: none; font-size: 1.5rem; }
    .card {
        background-color: var(--card-color); padding: 2rem; border-radius: 8px;
        box-shadow: 0 4px 8px var(--shadow-color); margin-bottom: 2rem;
        transition: background-color 0.3s, box-shadow 0.3s;
    }
    h2, h3 {
        color: var(--font-color); border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem; margin-top: 0;
    }
    .button-link {
        display: inline-block; background-color: var(--primary-color); color: white !important;
        padding: 0.8rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 1rem;
        font-weight: bold; text-decoration: none; text-align: center;
        transition: background-color 0.2s ease-in-out;
    }
    .button-link:hover { background-color: var(--primary-hover); }
    input[type="text"], input[type="email"], input[type="password"], input[type="url"], input[type="number"], select, input[type="file"] {
        width: 100%; padding: 0.8rem; margin-bottom: 1rem; border: 1px solid var(--border-color);
        border-radius: 4px; background-color: var(--input-bg); color: var(--font-color);
        box-sizing: border-box; transition: border-color 0.2s, box-shadow 0.2s;
    }
    input:focus, select:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25); outline: none;
    }
    input[type="submit"], button {
        background-color: var(--primary-color); color: white; padding: 0.8rem 1.5rem;
        border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; font-weight: bold;
        transition: background-color 0.2s ease-in-out;
    }
    input[type="submit"]:hover, button:hover { background-color: var(--primary-hover); }
    label { font-weight: bold; display: block; margin-bottom: 0.5rem; }
    .result {
        background-color: var(--bg-color); border-left: 4px solid var(--primary-color);
        padding: 1.5rem; margin-top: 1.5rem; word-wrap: break-word; overflow-x: auto;
    }
    .alert { padding: 1rem; border-radius: 4px; margin-bottom: 1rem; border: 1px solid transparent; }
    .alert-info { color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb; }
    .alert-warn { color: var(--alert-warn-text); background-color: var(--alert-warn-bg); border-color: var(--alert-warn-border); }
    body.dark-mode .alert-info { color: #bee5eb; background-color: #0c5460; border-color: #1c6470; }
    .task-list {
        list-style: none; padding: 0; display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem;
    }
    .task-list li a {
        display: block; background-color: var(--bg-color); padding: 1rem; border-radius: 4px;
        text-decoration: none; color: var(--primary-color); font-weight: bold;
        border: 1px solid var(--border-color); transition: all 0.2s ease-in-out;
    }
    .task-list li a:hover {
        transform: translateY(-3px); box-shadow: 0 4px 6px var(--shadow-color);
        border-color: var(--primary-color);
    }
    footer { text-align: center; margin-top: 2rem; color: #888; }
    .back-link { display: inline-block; margin-top: 2rem; color: var(--primary-color); text-decoration: none; }
    .switch { position: relative; display: inline-block; width: 50px; height: 24px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
        position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
        background-color: var(--switch-bg); transition: .4s; border-radius: 24px;
    }
    .slider:before {
        position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
        background-color: var(--switch-slider); transition: .4s; border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--primary-color); }
    input:checked + .slider:before { transform: translateX(26px); }
</style>
"""
THEME_SWITCH_JS = """
<script>
    const themeSwitch = document.getElementById('themeSwitch');
    function getTheme() { return localStorage.getItem('theme') || 'light'; }
    function setTheme(theme) {
        document.body.classList.toggle('dark-mode', theme === 'dark');
        if (themeSwitch) themeSwitch.checked = (theme === 'dark');
    }
    setTheme(getTheme());
    if (themeSwitch) {
        themeSwitch.addEventListener('change', (e) => {
            const newTheme = e.target.checked ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme);
            setTheme(newTheme);
        });
    }
</script>
"""
BASE_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title }}}} | Cognifyz Tasks</title>
    {BASE_CSS}
</head>
<body>
    <header>
        <h1><a href="/">Cognifyz Python Tasks</a></h1>
        <label class="switch">
            <input type="checkbox" id="themeSwitch">
            <span class="slider"></span>
        </label>
    </header>
    <main class="container">
        {{{{ content | safe }}}}
    </main>
    <footer><p>Built with Flask & ❤️</p></footer>
    {THEME_SWITCH_JS}
</body>
</html>
"""

# --- Helper Functions & Core Logic ---

def run_alibaba_scraper():
    """
    Launches Selenium to scrape RFQ data from Alibaba, using a local chromedriver.
    """
    try:
        driver_name = 'chromedriver.exe' if sys.platform.startswith('win') else 'chromedriver'
        chromedriver_path = os.path.join(BASE_DIR, driver_name)
        if not os.path.exists(chromedriver_path):
            return f"Error: ChromeDriver not found at {chromedriver_path}."
        service = Service(executable_path=chromedriver_path)
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        return f"Error: WebDriver failed to start. Details: {e}"

    # --- MODIFIED: Use the new target URL ---
    url = "https://i.alibaba.com/rfq-page"
    driver.get(url)
    
    time.sleep(5) 

    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1.5)
    time.sleep(3)
    
    # This selector is specific and may need to be updated for the new URL.
    cards = driver.find_elements(By.CSS_SELECTOR, "div.brh-rfq-item")
    if not cards:
        driver.quit()
        return "Error: No RFQ items found with the current selectors on this page. The page structure might be different from what the scraper expects."
    
    main_window = driver.current_window_handle
    results = []
    
    for idx, card in enumerate(cards[:10], 1): # Limit to 10 for demonstration
        try:
            soup = BeautifulSoup(card.get_attribute("outerHTML"), "lxml")
            data = {k: "N/A" for k in ["RFQ ID", "Title", "Buyer Name", "Buyer Image", "Inquiry Time", "Quotes Left", "Country", "Quantity Required", "Email Confirmed", "Experienced Buyer", "Inquiry URL", "Inquiry Date", "Scraping Date"]}

            title_tag = soup.select_one("a.brh-rfq-item__subject-link")
            if not title_tag: continue

            data["Title"] = title_tag.get_text(strip=True)
            data["Inquiry URL"] = "https:" + title_tag.get("href", "")
            
            if (buyer := soup.select_one("div.brh-rfq-item__other-info div.text")): data["Buyer Name"] = buyer.get_text(strip=True)
            if (buyer_img := soup.select_one("div.brh-rfq-item__other-info img")): data["Buyer Image"] = buyer_img.get('src')
            if (posted := soup.select_one("div.brh-rfq-item__publishtime")): data["Inquiry Time"] = posted.get_text(strip=True)
            data["Inquiry Date"] = data["Inquiry Time"]
            if (quote := soup.select_one("div.brh-rfq-item__quote-left span")): data["Quotes Left"] = quote.get_text(strip=True)
            if (country_img := soup.select_one("div.brh-rfq-item__country img")): data["Country"] = country_img.get('alt')
            
            data["Scraping Date"] = datetime.now().strftime("%Y-%m-%d")

            results.append(data)
        except Exception as e:
            print(f"Error processing card {idx}: {e}")
            continue
    
    driver.quit()

    if not results:
        return "Error: Scraped 0 RFQs. The selectors might be outdated for this page."

    df = pd.DataFrame(results)
    filename = f"alibaba_rfq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(os.path.join(SCRAPED_DATA_FOLDER, filename), index=False, encoding="utf-8-sig")
    
    return filename

def generate_visualization(df, plot_type, x_col, y_col, color_col):
    # ...This function remains unchanged...
    try:
        theme = request.cookies.get('theme', 'light')
        template = 'plotly_dark' if theme == 'dark' else 'plotly_white'
        fig = None
        if plot_type == 'scatter': fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"{y_col.title()} vs. {x_col.title()}", template=template)
        elif plot_type == 'bar': fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=f"Bar Chart of {y_col.title()} by {x_col.title()}", template=template)
        elif plot_type == 'line': fig = px.line(df, x=x_col, y=y_col, color=color_col, title=f"Line Chart of {y_col.title()} over {x_col.title()}", template=template)
        elif plot_type == 'histogram': fig = px.histogram(df, x=x_col, color=color_col, title=f"Histogram of {x_col.title()}", template=template)
        if fig:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color= 'var(--font-color)')
            return pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        return "<p>Invalid plot type selected.</p>"
    except Exception as e:
        return f"<p>Error generating plot: {e}. Please check your column selections.</p>"


# ... Other helper functions (reverse_string, calculate, etc.) remain unchanged ...
def reverse_string(s): return s[::-1]
def convert_temperature(value, unit):
    if unit == 'celsius': return f"{value}°C is {(value * 9/5) + 32:.2f}°F"
    if unit == 'fahrenheit': return f"{value}°F is {(value - 32) * 5/9:.2f}°C"
def validate_email(email): return "Valid Email" if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) else "Invalid Email"
def calculate(n1, n2, op):
    if op == '+': return n1 + n2
    if op == '-': return n1 - n2
    if op == '*': return n1 * n2
    if op == '/': return n1 / n2 if n2 != 0 else "Error: Division by zero"
def is_palindrome(s):
    cleaned = ''.join(filter(str.isalnum, s)).lower()
    return "It's a palindrome." if cleaned == cleaned[::-1] else "It's not a palindrome."
def check_password_strength(password):
    score = sum([1 if len(password) >= 8 else 0, 1 if re.search(r"[a-z]", password) else 0, 1 if re.search(r"[A-Z]", password) else 0, 1 if re.search(r"\d", password) else 0, 1 if re.search(r"\W", password) else 0])
    strength = {0: "Very Weak", 1: "Weak", 2: "Moderate", 3: "Strong", 4: "Very Strong", 5: "Excellent"}
    return f"Password strength: {strength.get(score)}"
def fibonacci_sequence(n):
    a, b = 0, 1; seq = []
    for _ in range(n): seq.append(a); a, b = b, a + b
    return seq
def count_words_in_file(file_content):
    words = re.findall(r'\b\w+\b', file_content.lower())
    return "<br>".join([f"'{w}': {c}" for w, c in sorted(Counter(words).items())])
def automate_csv_processing(df, column, operation):
    if column not in df.columns: return None, "Error: Column not found."
    if operation == 'uppercase': df[column] = df[column].astype(str).str.upper()
    elif operation == 'lowercase': df[column] = df[column].astype(str).str.lower()
    mem_file = io.BytesIO(); df.to_csv(mem_file, index=False, encoding='utf-8'); mem_file.seek(0)
    return mem_file, None


# --- Flask Routes ---
@app.route('/')
def home():
    # ... This route remains unchanged ...
    home_content = """<div class="card"><h2>Level 1 Tasks</h2><ul class="task-list"><li><a href="/level1/string-reversal">String Reversal</a></li><li><a href="/level1/temp-conversion">Temp Conversion</a></li><li><a href="/level1/email-validator">Email Validator</a></li><li><a href="/level1/calculator">Calculator</a></li><li><a href="/level1/palindrome">Palindrome Checker</a></li></ul></div><div class="card"><h2>Level 2 Tasks</h2><ul class="task-list"><li><a href="/level2/guessing-game">Guessing Game</a></li><li><a href="/level2/password-strength">Password Strength</a></li><li><a href="/level2/fibonacci">Fibonacci Sequence</a></li><li><a href="/level2/word-count">Word Count</a></li></ul></div><div class="card"><h2>Level 3 Tasks</h2><ul class="task-list"><li><a href="/scraper">Alibaba RFQ Scraper</a></li><li><a href="/level3/visualization">Data Visualization</a></li><li><a href="/level3/automation">CSV Task Automation</a></li></ul></div>"""
    return render_template_string(BASE_TEMPLATE, title="Home", content=home_content)

def render_task_page(title, description, form_content, result=None, is_file_upload=False):
    # ... This helper function remains unchanged ...
    enctype = 'enctype="multipart/form-data"' if is_file_upload else ""
    result_html = f'<div class="result"><h3>Result:</h3><div>{result}</div></div>' if result is not None else ""
    content = f"""<div class="card"><h2>{title}</h2><p>{description}</p><form method="post" {enctype}>{form_content}<br><input type="submit" value="Execute"></form>{result_html}</div><a href="/" class="back-link">&larr; Back to Home</a>"""
    return render_template_string(BASE_TEMPLATE, title=title, content=content)

# ... Level 1 & 2 Routes remain unchanged ...
@app.route('/level1/string-reversal', methods=['GET', 'POST'])
def l1_string_reversal():
    result = reverse_string(request.form['text']) if request.method == 'POST' else None
    form = '<label for="text">Enter text:</label><input type="text" name="text" required>'
    return render_task_page("String Reversal", "Reverses any text you enter.", form, result)
@app.route('/level1/temp-conversion', methods=['GET', 'POST'])
def l1_temp_conversion():
    result = None
    if request.method == 'POST':
        try: result = convert_temperature(float(request.form['value']), request.form['unit'])
        except ValueError: result = "Invalid input. Please enter a number."
    form = '<label for="value">Temperature:</label><input type="text" name="value" required><label for="unit">From Unit:</label><select name="unit"><option value="celsius">Celsius</option><option value="fahrenheit">Fahrenheit</option></select>'
    return render_task_page("Temperature Conversion", "Converts between Celsius and Fahrenheit.", form, result)
@app.route('/level1/email-validator', methods=['GET', 'POST'])
def l1_email_validator():
    result = validate_email(request.form['email']) if request.method == 'POST' else None
    form = '<label for="email">Enter an email:</label><input type="email" name="email" required>'
    return render_task_page("Email Validator", "Checks if an email address format is valid.", form, result)
@app.route('/level1/calculator', methods=['GET', 'POST'])
def l1_calculator():
    result = None
    if request.method == 'POST':
        try: result = calculate(float(request.form['n1']), float(request.form['n2']), request.form['op'])
        except ValueError: result = "Invalid input. Please enter numbers."
    form = '<label for="n1">Num 1:</label><input type="text" name="n1" required><label for="op">Operator:</label><select name="op"><option value="+">+</option><option value="-">-</option><option value="*">*</option><option value="/">/</option></select><label for="n2">Num 2:</label><input type="text" name="n2" required>'
    return render_task_page("Simple Calculator", "Performs basic arithmetic.", form, result)
@app.route('/level1/palindrome', methods=['GET', 'POST'])
def l1_palindrome():
    result = is_palindrome(request.form['text']) if request.method == 'POST' else None
    form = '<label for="text">Enter text:</label><input type="text" name="text" required>'
    return render_task_page("Palindrome Checker", "Checks if a word or phrase is the same forwards and backwards.", form, result)
@app.route('/level2/guessing-game', methods=['GET', 'POST'])
def l2_guessing_game():
    if 'number' not in session or request.method == 'GET': session['number'] = random.randint(1, 100)
    result = None
    if request.method == 'POST':
        try:
            guess = int(request.form['guess'])
            if guess < session['number']: result = "Too low!"
            elif guess > session['number']: result = "Too high!"
            else:
                result = f"Correct! The number was {session['number']}. New number chosen."
                session['number'] = random.randint(1, 100)
        except ValueError: result = "Please enter a number."
    form = '<label for="guess">Your Guess (1-100):</label><input type="number" name="guess" required>'
    return render_task_page("Guessing Game", "Guess the secret number between 1 and 100.", form, result)
@app.route('/level2/password-strength', methods=['GET', 'POST'])
def l2_password_strength():
    result = check_password_strength(request.form['password']) if request.method == 'POST' else None
    form = '<label for="password">Enter a password:</label><input type="password" name="password" required>'
    return render_task_page("Password Strength Checker", "Evaluates password strength.", form, result)
@app.route('/level2/fibonacci', methods=['GET', 'POST'])
def l2_fibonacci():
    result = None
    if request.method == 'POST':
        try: result = ", ".join(map(str, fibonacci_sequence(int(request.form['terms']))))
        except ValueError: result = "Please enter a positive integer."
    form = '<label for="terms">Number of terms:</label><input type="number" name="terms" min="1" required>'
    return render_task_page("Fibonacci Sequence", "Generates the Fibonacci sequence.", form, result)
@app.route('/level2/word-count', methods=['GET', 'POST'])
def l2_word_count():
    result = None
    if request.method == 'POST' and (file := request.files.get('file')):
        try: result = count_words_in_file(file.read().decode('utf-8'))
        except Exception as e: result = f"Error processing file: {e}"
    form = '<label for="file">Upload a text file:</label><input type="file" name="file" accept=".txt" required>'
    return render_task_page("Word Count in File", "Counts word occurrences in a .txt file.", form, result, True)


# --- Level 3 & Scraper Routes ---
@app.route('/scraper', methods=['GET', 'POST'])
def scraper_page():
    if request.method == 'POST':
        result_filename = run_alibaba_scraper()
        session['last_scrape_result'] = result_filename
        return redirect(url_for('scraper_results'))

    # --- MODIFIED: Updated instructions for the new URL ---
    content = """
    <div class="card">
        <h2>Alibaba RFQ Scraper</h2>
        <div class="alert alert-info">
            <strong>Prerequisites:</strong> Requires Google Chrome and a matching ChromeDriver in the app's folder.
        </div>
        <div class="alert alert-warn">
            <strong>Note:</strong> The scraper is designed for a specific HTML layout. If Alibaba has changed the `i.alibaba.com/rfq-page` layout, the scraper may fail to find data.
        </div>
        <h3>How to Use:</h3>
        <ol>
            <li>Click the button below to open the Alibaba RFQ page.</li>
            <li>In the <strong>new tab</strong>, log in to your account.</li>
            <li>After you see your RFQ dashboard, return to <strong>this tab</strong>.</li>
            <li>Click "Start Scraping". The process may take several minutes.</li>
        </ol>
        <p style="text-align:center; margin: 2rem 0;">
             <a href="https://i.alibaba.com/rfq-page" target="_blank" class="button-link" id="open-alibaba-btn">Step 1: Open Alibaba RFQ Page</a>
        </p>
        <form method="POST" style="text-align:center;">
            <button type="submit" id="start-scrape-btn">Step 2: Start Scraping</button>
        </form>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, title="Web Scraper", content=content)

@app.route('/scraper/results')
def scraper_results():
    # ... This route remains unchanged ...
    result = session.pop('last_scrape_result', None)
    if result and ".csv" in result:
        content = f"""<div class="card"><h2>Scraping Complete!</h2><p>The web scraper has finished. Download the data using the link below.</p><p style="text-align:center; margin-top: 2rem;"><a href="{url_for('download_scrape_file', filename=result)}" class="button-link">Download {result}</a></p><a href="/" class="back-link">&larr; Back to Home</a></div>"""
    else:
        content = f"""<div class="card"><h2>Scraping Failed</h2><div class="result"><strong>Details:</strong> {result or 'An unknown error occurred.'}</div><a href="{url_for('scraper_page')}" class="back-link">&larr; Try Again</a></div>"""
    return render_template_string(BASE_TEMPLATE, title="Scraper Results", content=content)

@app.route('/scraper/download/<path:filename>')
def download_scrape_file(filename):
    return send_from_directory(SCRAPED_DATA_FOLDER, filename, as_attachment=True)

@app.route('/level3/visualization', methods=['GET', 'POST'])
def l3_visualization():
    # ... This route remains unchanged ...
    plot_options = ""
    plot_div = ""
    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                filepath = os.path.join(UPLOAD_FOLDER, 'temp_data.csv')
                file.save(filepath)
                df = pd.read_csv(filepath)
                session['viz_columns'] = df.columns.tolist()
                session['viz_file'] = 'temp_data.csv'
            except Exception as e:
                plot_div = f"<div class='result'><strong>Error:</strong> Could not read CSV file. {e}</div>"
        elif 'generate_plot' in request.form and 'viz_file' in session:
            filepath = os.path.join(UPLOAD_FOLDER, session['viz_file'])
            df = pd.read_csv(filepath)
            plot_div = generate_visualization(df=df, plot_type=request.form.get('plot_type'), x_col=request.form.get('x_col'), y_col=request.form.get('y_col'), color_col=request.form.get('color_col') or None)
    if 'viz_columns' in session:
        cols = session['viz_columns']
        options_html = "".join([f'<option value="{c}">{c}</option>' for c in cols])
        plot_options = f"""<hr><label for="plot_type">Plot Type:</label><select name="plot_type"><option value="scatter">Scatter Plot</option><option value="bar">Bar Chart</option><option value="line">Line Chart</option><option value="histogram">Histogram</option></select><label for="x_col">X-Axis:</label><select name="x_col">{options_html}</select><label for="y_col">Y-Axis (not for Histogram):</label><select name="y_col">{options_html}</select><label for="color_col">Color By (Optional):</label><select name="color_col"><option value="">None</option>{options_html}</select><br><button type="submit" name="generate_plot" value="1">Generate Plot</button>"""
    content = f"""<div class="card"><h2>Data Visualization Tool</h2><p>Upload a CSV file to generate interactive plots.</p><form method="post" enctype="multipart/form-data"><label for="file">1. Upload CSV File:</label><input type="file" name="file" accept=".csv" onchange="this.form.submit()">{plot_options}</form>{ '<div class="result">' + plot_div + '</div>' if plot_div else '' }</div><a href="/" class="back-link">&larr; Back to Home</a>"""
    return render_template_string(BASE_TEMPLATE, title="Data Visualization", content=content)

@app.route('/level3/automation', methods=['GET', 'POST'])
def l3_automation():
    # ... This route remains unchanged ...
    if request.method == 'POST':
        if not (file := request.files.get('file')): return "No file selected", 400
        try:
            df = pd.read_csv(file)
            processed_file, error = automate_csv_processing(df, request.form.get('column'), request.form.get('operation'))
            if error: return error, 400
            return send_file(processed_file, as_attachment=True, download_name='processed_data.csv', mimetype='text/csv')
        except Exception as e: return f"Error processing file: {e}", 500
    form = """<label for="file">Upload a CSV file:</label><input type="file" name="file" accept=".csv" required><label for="column">Column Name to Process:</label><input type="text" name="column" required><label for="operation">Operation:</label><select name="operation"><option value="uppercase">Convert to Uppercase</option><option value="lowercase">Convert to Lowercase</option></select>"""
    return render_task_page("CSV Task Automation", "Automates text transformations on a CSV column.", form, None, True)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
