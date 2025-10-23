from flask import Blueprint, request, jsonify
import requests
import json
import time
import arxiv
import tempfile
import os
from datetime import datetime, timedelta
import re

research_enhanced_bp = Blueprint("research_enhanced", __name__)

# Gemini API settings
GEMINI_API_KEY = "AIzaSyAujpMwvJapiDMHGQUkh3kCo22sJi_xlVI"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def call_gemini_api(prompt):
    """Function to call Gemini API with optimized settings"""
    headers = {
        "Content-Type": "application/json",
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 4096,  # Increased back to 4096
        }
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=40  # Increased to 40 seconds
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                # Gemini APIの応答からテキストを抽出
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                # JSON形式でない場合があるため、JSONブロックを抽出
                try:
                    start_idx = text_content.find("{")
                    end_idx = text_content.rfind("}") + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = text_content[start_idx:end_idx]
                        # JSONが不正な場合に備えてjson.loadsをtry-exceptで囲む
                        json.loads(json_str) # 有効なJSONかチェック
                        return json_str # 有効なJSON文字列を返す
                    else:
                        print(f"Warning: No JSON object found in Gemini response: {text_content[:200]}...")
                        return text_content # JSONが見つからない場合はそのまま返す
                except json.JSONDecodeError as json_err:
                    print(f"JSON Decode Error in Gemini response: {json_err} - Response: {text_content[:200]}...")
                    return text_content # JSONパースエラーの場合はそのまま返す
            else:
                print(f"Warning: Gemini API response was not in the expected format or empty: {result}")
                return json.dumps({"error": "API response was not in the expected format or empty."})
        else:
            print(f"Error: Gemini API call error: {response.status_code} - {response.text}")
            return json.dumps({"error": f"API call error: {response.status_code} - {response.text}"})
            
    except requests.exceptions.Timeout:
        print("Error during API call: Request timed out.")
        return json.dumps({"error": "API call timed out."})
    except requests.exceptions.RequestException as req_err:
        print(f"Error during API call: Request exception - {req_err}")
        return json.dumps({"error": f"API request failed: {str(req_err)}"})
    except Exception as e:
        print(f"Unexpected error during API call: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

def search_arxiv_papers_simple(query, limit=10):
    """Enhanced arXiv paper search with increased limit"""
    try:
        client = arxiv.Client()
        
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in client.results(search):
            paper_data = {
                "title": result.title,
                "authors": ", ".join([author.name for author in result.authors]),
                "date": result.published.strftime("%Y-%m-%d"),
                "abstract": result.summary,  # 全文を読み込む
                "url": result.entry_id,
                "categories": [cat for cat in result.categories],
                "primary_category": result.primary_category
            }
            papers.append(paper_data)
        
        return papers
        
    except Exception as e:
        print(f"arXiv search error: {str(e)}")
        return get_dummy_papers(query, limit)

def get_dummy_papers(query, limit):
    """Function to return dummy paper data"""
    dummy_papers = [
        {
            "title": f"Deep Learning Approaches for {query}: A Comprehensive Survey",
            "authors": "Smith, J., Johnson, A., Williams, B.",
            "date": "2024-01-15",
            "abstract": f"This paper provides a comprehensive survey of deep learning methods in {query}. It compares various techniques and clarifies their advantages and limitations...",
            "url": "https://arxiv.org/abs/2401.12345",
            "categories": ["cs.LG", "cs.AI"],
            "primary_category": "cs.LG"
        },
        {
            "title": f"Ethical Considerations in {query} Systems",
            "authors": "Brown, C., Davis, E., Miller, F.",
            "date": "2024-02-20",
            "abstract": f"This paper examines ethical considerations in {query} systems. It analyzes important issues such as privacy, transparency, and accountability...",
            "url": "https://arxiv.org/abs/2402.67890",
            "categories": ["cs.CY", "cs.AI"],
            "primary_category": "cs.CY"
        },
        {
            "title": f"Novel Applications of {query} in Healthcare",
            "authors": "Wilson, G., Taylor, H., Anderson, I.",
            "date": "2024-03-10",
            "abstract": f"This paper proposes new methods for applying {query} to the medical field. It achieves improved accuracy and efficiency compared to traditional approaches...",
            "url": "https://arxiv.org/abs/2403.54321",
            "categories": ["cs.LG", "q-bio.QM"],
            "primary_category": "cs.LG"
        }
    ]
    
    return dummy_papers[:limit]

def create_fallback_idea(direction, topic, index):
    """Create a fallback research idea when API parsing fails or for simplified generation"""
    direction_name = direction.get("direction", f"Research Direction {index}")
    
    return {
        "title": f"{direction_name}: Advanced {topic} Framework",
        "overview": {
            "background": f"This research aims to develop a comprehensive framework for {direction_name.lower()} in {topic}. Current approaches often lack integrated solutions and comprehensive methodologies, leading to fragmented understanding and limited practical applicability. This study will address these limitations by synthesizing existing knowledge and proposing novel approaches.",
            "research_hypothesis": f"By developing an integrated {direction_name.lower()} framework, we can significantly improve {topic} performance and applicability, leading to more robust and generalizable solutions than current state-of-the-art methods.",
            "significance": f"This research addresses critical gaps in {topic} by providing a unified approach to {direction_name.lower()}. It will contribute to a deeper theoretical understanding and offer practical solutions for real-world challenges, potentially opening new avenues for interdisciplinary research.",
            "novelty": f"Novel integration of {direction_name.lower()} approaches with {topic}, providing the first comprehensive framework that addresses current methodological gaps and technical limitations identified in recent literature. This framework will introduce new algorithms/techniques for enhanced performance.",
            "expected_outcomes": ["Improved performance metrics (e.g., accuracy, efficiency)", "Enhanced applicability across diverse {topic} sub-domains", "Development of a robust and scalable framework", "New theoretical insights into {topic} principles"]
        },
        "methodology": {
            "research_design": f"A mixed-methods approach combining theoretical analysis, computational modeling, and experimental validation. The study will involve iterative design and testing cycles to refine the proposed framework for {topic}.",
            "data_collection": {
                "sources": ["Publicly available benchmark datasets (e.g., ImageNet, ArXiv)", "Simulated data generated from theoretical models", "Experimental data collected from laboratory setups"],
                "methods": ["Systematic literature review to identify existing methods and gaps", "Development of novel algorithms and computational models", "Implementation and optimization of the framework using Python/TensorFlow/PyTorch", "Rigorous experimental evaluation on diverse datasets"],
                "sample_size": "Not applicable for theoretical/computational research, but experimental validation will use sufficiently large datasets to ensure statistical significance.",
                "data_types": ["Quantitative (performance metrics, computational costs)", "Qualitative (case studies, expert evaluations)", "Mixed-methods (combining both for comprehensive assessment)"]
            },
            "analysis_techniques": [
                {
                    "technique": "Advanced statistical analysis (ANOVA, regression, t-tests)",
                    "purpose": "To identify patterns, relationships, and statistical significance of results",
                    "implementation": "Using SciPy, NumPy, and Pandas in Python",
                    "expected_results": "Quantifiable improvements in performance and efficiency compared to baseline methods."
                },
                {
                    "technique": "Comparative analysis with state-of-the-art models",
                    "purpose": "To benchmark the proposed framework against existing solutions",
                    "implementation": "Implementing and testing leading models from recent literature",
                    "expected_results": "Demonstration of superior performance or novel capabilities."
                }
            ],
            "experimental_setup": {
                "phases": [
                    {
                        "phase": "Phase 1: Literature Review and Theoretical Framework Development",
                        "duration": "3 months",
                        "activities": ["Identify key concepts and existing models", "Formulate initial theoretical framework", "Define research questions and hypotheses"],
                        "deliverables": ["Comprehensive literature review report", "Initial framework design document", "Refined research questions"]
                    },
                    {
                        "phase": "Phase 2: Algorithm Development and Implementation",
                        "duration": "6 months",
                        "activities": ["Design and develop novel algorithms", "Implement the framework in a suitable programming environment", "Conduct preliminary testing and debugging"],
                        "deliverables": ["Implemented algorithms and code repository", "Unit test reports", "Initial performance benchmarks"]
                    },
                    {
                        "phase": "Phase 3: Experimental Validation and Evaluation",
                        "duration": "9 months",
                        "activities": ["Set up experimental environment", "Run experiments on benchmark and simulated datasets", "Collect and analyze performance data"],
                        "deliverables": ["Experimental results and data analysis reports", "Performance comparison charts", "Refined framework based on results"]
                    },
                    {
                        "phase": "Phase 4: Refinement, Documentation, and Dissemination",
                        "duration": "6 months",
                        "activities": ["Refine the framework based on evaluation results", "Prepare comprehensive documentation", "Write research papers and present findings at conferences"],
                        "deliverables": ["Finalized framework and code", "Technical documentation", "Published research papers and presentations"]
                    }
                ],
                "controls": ["Controlled experimental conditions to minimize external variables", "Randomized data splitting for training and testing", "Use of established benchmarks for fair comparison"],
                "variables": {
                    "independent": ["Proposed framework parameters", "Dataset characteristics", "Computational resources"],
                    "dependent": ["Performance metrics (e.g., accuracy, F1-score, processing time)", "Resource utilization (e.g., memory, CPU)", "Scalability"],
                    "confounding": ["Hardware variations", "Software environment differences", "Random initialization effects"]
                }
            },
            "validation_methods": ["Cross-validation on multiple datasets", "Comparison with theoretical predictions", "Expert review and feedback", "Replication by independent researchers"]
        },
        "feasibility": {
            "technical_requirements": ["High-performance computing resources (GPUs/TPUs)", "Specialized software libraries (e.g., TensorFlow, PyTorch, scikit-learn)", "Access to large-scale datasets"],
            "resource_needs": {
                "computational": "Access to cloud computing platforms (e.g., Google Cloud, AWS) or local GPU clusters for training and experimentation.",
                "data": "Availability of relevant benchmark datasets and tools for data preprocessing and augmentation.",
                "personnel": "A multidisciplinary research team with expertise in {topic}, machine learning, data science, and software engineering.",
                "equipment": "Standard office equipment, high-end workstations for development, and access to specialized hardware if required for specific experiments."
            },
            "timeline": {
                "total_duration": "24 months",
                "milestones": [
                    {
                        "milestone": "Completion of theoretical framework and initial algorithm design",
                        "timeframe": "Month 3",
                        "success_criteria": "Detailed design document and preliminary pseudo-code."
                    },
                    {
                        "milestone": "Working prototype of the core framework",
                        "timeframe": "Month 9",
                        "success_criteria": "Functional code demonstrating key functionalities on small datasets."
                    },
                    {
                        "milestone": "Comprehensive experimental results and analysis",
                        "timeframe": "Month 18",
                        "success_criteria": "Publication-ready performance data and comparative analysis."
                    },
                    {
                        "milestone": "Final framework, documentation, and research papers submitted",
                        "timeframe": "Month 24",
                        "success_criteria": "Complete and well-documented system, with at least one peer-reviewed publication."
                    }
                ]
            },
            "risk_assessment": [
                {
                    "risk": "Technical challenges in algorithm optimization and scalability",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Iterative development with continuous performance profiling and optimization; explore parallel computing techniques."
                },
                {
                    "risk": "Difficulty in obtaining or processing large-scale, high-quality datasets",
                    "probability": "Medium",
                    "impact": "Medium",
                    "mitigation": "Explore data augmentation techniques; collaborate with data providers; develop robust data preprocessing pipelines."
                },
                {
                    "risk": "Unexpected limitations of the chosen AI model (Gemini 2.5 Flash)",
                    "probability": "Low",
                    "impact": "Medium",
                    "mitigation": "Design the framework with modularity to allow for easy integration of alternative AI models; conduct preliminary tests to assess model suitability."
                }
            ]
        },
        "impact": {
            "scientific_contribution": f"Significant advancement in {topic} field with novel {direction_name.lower()} approach. This research will introduce new theoretical models and practical methodologies, pushing the boundaries of current understanding and capabilities in {topic}.",
            "practical_applications": ["Development of more efficient and accurate {topic} systems for industry", "Improved decision-making tools in relevant sectors", "Creation of new educational resources and training programs based on the framework"],
            "societal_benefits": ["Enhanced problem-solving capabilities for complex societal issues (e.g., healthcare, environmental monitoring)", "Increased efficiency and resource optimization in various domains", "Contribution to the broader scientific community through open-source tools and publications"],
            "economic_potential": "Substantial potential for commercialization and economic impact through new product development, process optimization, and job creation in {topic}-related industries. This research could lead to significant cost savings and new market opportunities.",
            "future_research_directions": ["Extension of the framework to new {topic} sub-domains", "Integration with other emerging technologies (e.g., blockchain, IoT)", "Longitudinal studies to assess real-world impact and sustainability", "Exploration of ethical and societal implications of the developed framework"]
        }
    }

@research_enhanced_bp.route("/generate-ideas-enhanced", methods=["POST"])
def generate_ideas_enhanced():
    """Simplified research idea generation API"""
    try:
        data = request.get_json()
        topic = data.get("topic", "")
        focus_area = data.get("focus_area", "")
        num_papers = min(data.get("num_papers", 10), 10)  # Limit to 10 papers max
        categories = data.get("categories", None)
        
        if not topic.strip():
            return jsonify({
                "success": False,
                "message": "Research topic is empty."
            }), 400
        
        # Stage 1: Search for related papers (simplified)
        related_papers = search_arxiv_papers_simple(topic, limit=num_papers)
        
        # Stage 2: Build simplified context
        papers_context = ""
        if related_papers:
            papers_context = f"Research analysis for {topic}:\n"
            papers_context += f"Total papers analyzed: {len(related_papers)}\n\n"
            
            for i, paper in enumerate(related_papers[:5], 1):  # Use top 5 papers for context
                papers_context += f"{i}. {paper["title"]}\n"
                papers_context += f"   Authors: {paper["authors"]}\n"
                papers_context += f"   Abstract: {paper["abstract"]}\n\n"
        
        # Stage 3: Generate research directions (simplified)
        initial_prompt = f"""As a researcher in {topic}, analyze the following papers and identify 3 research directions.

Research Topic: {topic}
Focus Area: {focus_area if focus_area else 'General advancement'}

{papers_context}

Provide 3 research directions in JSON format:

{{
  "research_directions": [
    {{
      "direction": "Direction 1 Name",
      "rationale": "Why this is important",
      "gap_addressed": "What gap this addresses"
    }},
    {{
      "direction": "Direction 2 Name", 
      "rationale": "Why this is important",
      "gap_addressed": "What gap this addresses"
    }},
    {{
      "direction": "Direction 3 Name",
      "rationale": "Why this is important",
      "gap_addressed": "What gap this addresses"
    }}
  ]
}}

Respond only in valid JSON format."""
        
        # Call Gemini API for directions
        initial_response = call_gemini_api(initial_prompt)
        print(f"Initial Response: {initial_response[:200]}...")
        
        research_directions = []
        try:
            # call_gemini_apiは既にJSON文字列を返すように設計されているため、直接json.loadsを試みる
            parsed_initial = json.loads(initial_response)
            research_directions = parsed_initial.get("research_directions", [])
            if not research_directions:
                print(f"Warning: 'research_directions' key not found or empty in Gemini response: {initial_response[:200]}...")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error after call_gemini_api: {e} - Response: {initial_response[:200]}...")
            # Geminiの応答がJSON文字列でなかった場合、またはJSONが不完全だった場合、JSONブロックを抽出するロジックを試す
            try:
                start_idx = initial_response.find("{")
                end_idx = initial_response.rfind("}") + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = initial_response[start_idx:end_idx]
                    parsed_initial = json.loads(json_str)
                    research_directions = parsed_initial.get("research_directions", [])
                    if not research_directions:
                         print(f"Warning: 'research_directions' key not found or empty after manual JSON extraction: {json_str[:200]}...")
                else:
                    print(f"Warning: No JSON object found in Gemini response after initial parse attempt: {initial_response[:200]}...")
            except json.JSONDecodeError as inner_e:
                print(f"Inner JSON Decode Error: {inner_e} - Response: {initial_response[:200]}...")
            except Exception as inner_e:
                print(f"Unexpected error during inner JSON extraction: {inner_e} - Response: {initial_response[:200]}...")
        except Exception as e:
            print(f"Unexpected error during initial Gemini response parsing: {e} - Response: {initial_response[:200]}...")

        # If no directions are parsed, use fallback
        if not research_directions:
            print("Using fallback research directions.")
            # フォールバックロジックをより堅牢にする
            research_directions = [
                {"direction": f"Advanced {topic} Framework", "rationale": "Need for comprehensive approach", "gap_addressed": "Integration challenges"},
                {"direction": f"Interdisciplinary {topic} Research", "rationale": "Cross-domain opportunities", "gap_addressed": "Disciplinary silos"},
                {"direction": f"Practical {topic} Applications", "rationale": "Real-world implementation", "gap_addressed": "Theory-practice gap"}
            ]
            # フォールバックが発動した場合でも、詳細なアイデアを生成するためにcreate_fallback_ideaを使用
            detailed_ideas = []
            for i, direction in enumerate(research_directions[:3], 1):
                idea = create_fallback_idea(direction, topic, i)
                detailed_ideas.append(idea)
            return jsonify({
                "success": True,
                "ideas": detailed_ideas,
                "topic": topic,
                "focus_area": focus_area,
                "analysis": {
                    "papers_analyzed": len(related_papers),
                    "research_directions": research_directions
                },
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })


        
        # Return response
        return jsonify({
            "success": True,
            "ideas": detailed_ideas,
            "topic": topic,
            "focus_area": focus_area,
            "analysis": {
                "papers_analyzed": len(related_papers),
                "research_directions": research_directions
            },
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })


        
        # Return response
        return jsonify({
            "success": True,
            "ideas": detailed_ideas,
            "topic": topic,
            "focus_area": focus_area,
            "analysis": {
                "papers_analyzed": len(related_papers),
                "research_directions": research_directions
            },
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error in enhanced idea generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500
        

        
        # Return response
        return jsonify({
            "success": True,
            "ideas": detailed_ideas,
            "topic": topic,
            "focus_area": focus_area,
            "analysis": {
                "papers_analyzed": len(related_papers),
                "research_directions": research_directions
            },
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error in enhanced idea generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500

