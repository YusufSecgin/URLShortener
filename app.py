from flask import Flask, request, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
import validators

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class URLMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_url = db.Column(db.String(6), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

def generate_short_url(original_url):
    hash_object = hashlib.md5(original_url.encode())
    return hash_object.hexdigest()[:6]  # İlk 6 karakter

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form.get('url')
    
    if not original_url or not validators.url(original_url):
        return jsonify({"error": "Valid URL is required"}), 400

    short_url = generate_short_url(original_url)
    while URLMapping.query.filter_by(short_url=short_url).first():
        original_url += "1"  # Çakışma durumunda orijinal URL'yi değiştir
        short_url = generate_short_url(original_url)

    new_url = URLMapping(original_url=original_url, short_url=short_url)
    db.session.add(new_url)
    db.session.commit()

    return render_template('index.html', short_url=f"http://127.0.0.1:5000/{short_url}")

@app.route('/<short_url>', methods=['GET'])
def redirect_to_url(short_url):
    url_mapping = URLMapping.query.filter_by(short_url=short_url).first()

    if url_mapping:
        url_mapping.clicks += 1
        db.session.commit()
        return redirect(url_mapping.original_url)
    else:
        return jsonify({"error": "URL not found"}), 404

@app.route('/analytics/<short_url>', methods=['GET'])
def analytics(short_url):
    url_mapping = URLMapping.query.filter_by(short_url=short_url).first()

    if url_mapping:
        return jsonify({
            "original_url": url_mapping.original_url,
            "short_url": url_mapping.short_url,
            "clicks": url_mapping.clicks
        })
    else:
        return jsonify({"error": "URL not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
