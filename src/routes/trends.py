from flask import Blueprint, request, jsonify
import arxiv
from collections import Counter
import json
import requests

trends_bp = Blueprint("trends", __name__)

@trends_bp.route("/analyze-trends", methods=["POST"])
def analyze_trends():
    data = request.get_json()
    topic = data.get("topic", "AI")
    
    try:
        # 1. arXivから論文データを収集
        search = arxiv.Search(
            query=topic,
            max_results=50,
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
        
        # 2. 簡単な分析
        # 年別論文数
        year_counts = {}
        for paper in papers:
            year = paper["published"]
            year_counts[year] = year_counts.get(year, 0) + 1
        
        # 上位著者
        all_authors = [author for paper in papers for author in paper["authors"]]
        top_authors = Counter(all_authors).most_common(10)
        
        # 上位キーワード（簡単な実装）
        all_abstracts = ' '.join([paper['abstract'] for paper in papers])
        words = all_abstracts.lower().split()
        # 簡単なフィルタリング
        filtered_words = [word for word in words if len(word) > 3 and word.isalpha()]
        top_keywords = Counter(filtered_words).most_common(20)

        return jsonify({
            "success": True,
            "topic": topic,
            "analysis": {
                "papers_analyzed": len(papers),
                "year_distribution": year_counts,
                "top_authors": top_authors,
                "top_keywords": top_keywords
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


