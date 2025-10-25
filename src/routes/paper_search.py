from flask import Blueprint, request, jsonify
import arxiv

paper_search_bp = Blueprint("paper_search", __name__)

@paper_search_bp.route("/api/search-papers", methods=["POST"])
def search_papers():
    data = request.get_json()
    query = data.get("query", "")
    author = data.get("author", "")
    max_results = data.get("max_results", 10)

    search_query = []
    if query:
        search_query.append(f'all:"{query}"')
    if author:
        search_query.append(f'au:"{author}"')

    if not search_query:
        return jsonify({"success": False, "error": "Please provide a search query or author."})

    final_query = " AND ".join(search_query)

    try:
        search = arxiv.Search(
            query=final_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        papers = []
        for result in arxiv.Client().results(search):
            papers.append({
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "published": result.published.strftime("%Y-%m-%d"),
                "abstract": result.summary,
                "url": result.entry_id,
                "categories": result.categories
            })

        return jsonify({"success": True, "papers": papers})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


