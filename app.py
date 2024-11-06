# app.py
from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import db, User,PDFDocument
import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.document_loaders import PyMuPDFLoader
from langchain.docstore.document import Document
from langchain import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain


load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
llm = ChatGoogleGenerativeAI(model="gemini-pro")


db_api_key = os.getenv("DB_API")
key = os.getenv("key")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_api_key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = key
app.config['UPLOAD_FOLDER'] = 'uploads'  # Define the upload folder path


# Initialize the database with the Flask app
db.init_app(app)

# Command to create the database tables
@app.cli.command('create_db')
def create_database():
    """Create database tables."""
    with app.app_context():
        db.create_all()  # Creates tables using db.Model-defined models
        print("Database tables created successfully.")

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        password_hash = generate_password_hash(password)

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User already exists, please login.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

# Route for dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    # Fetch the current user
    user = User.query.get(session['user_id'])
    
    return render_template('dashboard.html', current_user=user)
# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



# Route to display PDF upload form and process summarization
@app.route('/upload_pdf', methods=['GET', 'POST'])
def upload_pdf():
    summary = None
    if request.method == 'POST':
        file = request.files['file']
        
        # Secure the filename and save it
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Load and extract content from PDF
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()
            document = [Document(page_content=doc.page_content) for doc in docs]

            # Define prompt for summarization
            template = '''Write a concise and short summary of the following text in 300 words.
            Text: `{document}`
            '''
            prompt = PromptTemplate(input_variables=['document'], template=template)
            llm_chain = LLMChain(llm=llm, prompt=prompt)
            stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="document")
            
            # Run summarization chain
            output_summary = stuff_chain.invoke(document)
            summary = output_summary["output_text"]

            # Save PDF file path and summary to database
            pdf_document = PDFDocument(filename=filename, data=file.read(), summary=summary)
            db.session.add(pdf_document)
            db.session.commit()

            flash('File uploaded and summarized successfully.', 'success')
        else:
            flash('Only PDF files are allowed.', 'danger')
    
    # Render upload page with the summary if generated
    return render_template('upload_pdf.html', summary=summary)
    
if __name__ == '__main__':
    app.run(debug=True)
