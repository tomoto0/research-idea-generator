from flask import Blueprint, request, jsonify
import arxiv
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import io
import base64
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

trends_bp = Blueprint("trends", __name__)

# NLTKのストップワードをダウンロード（初回のみ）
import nltk
nltk.download('stopwords')
nltk.download('punkt')

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    return filtered_tokens

@trends_bp.route("/api/analyze-trends", methods=["POST"])
def analyze_trends():
    data = request.get_json()
    topic = data.get("topic", "AI")
    
    # 1. arXivから論文データを収集
    search = arxiv.Search(
        query=topic,
        max_results=100, # トレンド分析のため多めに取得
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    papers = []
    for result in arxiv.Client().results(search):
        papers.append({
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published": result.published.year,
            "abstract": result.summary,
            "primary_category": result.primary_category
        })
    
    df = pd.DataFrame(papers)
    
    # 2. データ分析
    # 年別論文数
    publication_trend = df.groupby('published').size()
    
    # 上位著者
    all_authors = [author for sublist in df['authors'] for author in sublist]
    top_authors = Counter(all_authors).most_common(10)
    
    # 上位キーワード
    all_abstracts = ' '.join(df['abstract'])
    keywords = preprocess_text(all_abstracts)
    top_keywords = Counter(keywords).most_common(20)

    # 3. 可視化
    # 年別論文数のグラフ
    plt.figure(figsize=(10, 5))
    plt.plot(publication_trend.index, publication_trend.values, marker='o')
    plt.title(f'Publication Trend for "{topic}"')
    plt.xlabel('Year')
    plt.ylabel('Number of Papers')
    plt.grid(True)
    img_io = io.BytesIO()
    plt.savefig(img_io, format='PNG', bbox_inches='tight')
    img_io.seek(0)
    pub_trend_img = base64.b64encode(img_io.getvalue()).decode('utf-8')
    plt.close()

    # 4. 結果をJSONで返す
    return jsonify({
        "success": True,
        "topic": topic,
        "analysis": {
            "papers_analyzed": len(df),
            "publication_trend_chart": pub_trend_img,
            "top_authors": top_authors,
            "top_keywords": top_keywords
        }
    })


