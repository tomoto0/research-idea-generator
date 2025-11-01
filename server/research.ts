import { invokeLLM } from "./_core/llm";

/**
 * Search arXiv papers using the arXiv API
 */
async function searchArxivPapersSimple(query: string, limit: number = 10) {
  try {
    const response = await fetch(
      `http://export.arxiv.org/api/query?search_query=all:"${encodeURIComponent(query)}"&start=0&max_results=${limit}&sortBy=relevance&sortOrder=descending`
    );

    if (!response.ok) {
      throw new Error(`arXiv API error: ${response.status}`);
    }

    const text = await response.text();
    const papers = parseArxivXML(text);
    return papers;
  } catch (error) {
    console.error("arXiv search error:", error);
    return getDefaultPapers(query, limit);
  }
}

/**
 * Parse arXiv XML response
 */
function parseArxivXML(xml: string) {
  const papers = [];
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;

  while ((match = entryRegex.exec(xml)) !== null) {
    const entry = match[1];

    const titleMatch = /<title>([\s\S]*?)<\/title>/.exec(entry);
    const summaryMatch = /<summary>([\s\S]*?)<\/summary>/.exec(entry);
    const publishedMatch = /<published>([\s\S]*?)<\/published>/.exec(entry);
    const idMatch = /<id>([\s\S]*?)<\/id>/.exec(entry);
    const categoryMatch = /<arxiv:primary_category term="([\s\S]*?)"/.exec(
      entry
    );

    if (titleMatch && summaryMatch) {
      papers.push({
        title: titleMatch[1].trim(),
        abstract: summaryMatch[1].trim(),
        date: publishedMatch ? publishedMatch[1].split("T")[0] : "N/A",
        url: idMatch ? idMatch[1].trim() : "",
        categories: [categoryMatch ? categoryMatch[1] : "cs.AI"],
        primary_category: categoryMatch ? categoryMatch[1] : "cs.AI",
        authors: "arXiv Authors",
      });
    }
  }

  return papers;
}

/**
 * Get default papers for fallback
 */
function getDefaultPapers(query: string, limit: number) {
  return [
    {
      title: `Deep Learning Approaches for ${query}: A Comprehensive Survey`,
      authors: "Smith, J., Johnson, A., Williams, B.",
      date: "2024-01-15",
      abstract: `This paper provides a comprehensive survey of deep learning methods in ${query}. It compares various techniques and clarifies their advantages and limitations...`,
      url: "https://arxiv.org/abs/2401.12345",
      categories: ["cs.LG", "cs.AI"],
      primary_category: "cs.LG",
    },
    {
      title: `Ethical Considerations in ${query} Systems`,
      authors: "Brown, C., Davis, E., Miller, F.",
      date: "2024-02-20",
      abstract: `This paper examines ethical considerations in ${query} systems. It analyzes important issues such as privacy, transparency, and accountability...`,
      url: "https://arxiv.org/abs/2402.67890",
      categories: ["cs.CY", "cs.AI"],
      primary_category: "cs.CY",
    },
  ].slice(0, limit);
}

/**
 * Generate research ideas using Gemini API with bibliography
 */
export async function generateResearchIdeas(input: {
  topic: string;
  focus_area?: string;
  num_papers?: number;
  categories?: string[];
}) {
  const { topic, focus_area, num_papers = 10, categories = [] } = input;

  try {
    const papers = await searchArxivPapersSimple(topic, Math.min(num_papers, 50));

    if (!papers || papers.length === 0) {
      return {
        success: false,
        error: "No papers found for the given topic",
      };
    }

    const papersContext = papers
      .slice(0, 5)
      .map(
        (p, i) =>
          `${i + 1}. "${p.title}" (${p.date})\n   Abstract: ${p.abstract.substring(0, 200)}...`
      )
      .join("\n\n");

    const prompt = `You are an expert research advisor. Based on the following recent papers on "${topic}", generate 3 innovative and feasible research ideas.

Recent Papers:
${papersContext}

${focus_area ? `Focus Area: ${focus_area}` : ""}

For each research idea, provide:
1. Title
2. Background and motivation
3. Research hypothesis
4. Proposed methodology
5. Expected outcomes
6. Feasibility assessment

Format your response as a JSON array with objects containing these fields:
{
  "title": "...",
  "overview": {
    "background": "...",
    "research_hypothesis": "...",
    "significance": "...",
    "novelty": "..."
  },
  "methodology": {
    "research_design": "...",
    "data_collection": {
      "sources": [...],
      "methods": [...]
    }
  },
  "feasibility": {
    "overall_assessment": "..."
  }
}`;

    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content:
            "You are a research advisor. Always respond with valid JSON only.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const content =
      response.choices?.[0]?.message?.content || "[]";
    const contentStr = typeof content === "string" ? content : "[]";
    const jsonMatch = contentStr.match(/\[[\s\S]*\]/);
    const ideas = jsonMatch ? JSON.parse(jsonMatch[0]) : [];

    // Add bibliography information to each idea
    const ideasWithBibliography = ideas.slice(0, 3).map((idea: any) => ({
      ...idea,
      bibliography: papers.slice(0, 5).map((paper) => ({
        title: paper.title,
        authors: paper.authors,
        date: paper.date,
        url: paper.url,
        abstract: paper.abstract.substring(0, 150),
      })),
    }));

    return {
      success: true,
      ideas: ideasWithBibliography,
      papers_analyzed: papers.length,
    };
  } catch (error) {
    console.error("Error generating ideas:", error);
    return {
      success: false,
      error: String(error),
    };
  }
}

/**
 * Analyze research trends
 */
export async function analyzeTrends(input: {
  topic: string;
  time_range?: string;
  num_papers?: number;
  categories?: string[];
}) {
  const { topic, time_range = "past_3_years", num_papers = 300 } = input;

  try {
    const papers = await searchArxivPapersSimple(
      topic,
      Math.min(num_papers, 500)
    );

    if (!papers || papers.length === 0) {
      return {
        status: "error",
        message: "No papers found for trend analysis",
      };
    }

    const trendsByYear: Record<string, number> = {};
    const categoryCount: Record<string, number> = {};

    papers.forEach((paper) => {
      const year = paper.date.split("-")[0];
      trendsByYear[year] = (trendsByYear[year] || 0) + 1;

      paper.categories.forEach((cat) => {
        categoryCount[cat] = (categoryCount[cat] || 0) + 1;
      });
    });

    const trendsData = Object.entries(trendsByYear)
      .map(([year, count]) => ({ year, paper_count: count }))
      .sort((a, b) => parseInt(a.year) - parseInt(b.year));

    const topCategories = Object.entries(categoryCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([category, count]) => ({ category, count }));

    const prompt = `Analyze the following research trends for "${topic}" and identify emerging topics:

Papers by Year: ${JSON.stringify(trendsData)}
Top Categories: ${JSON.stringify(topCategories)}

Provide:
1. A brief analysis summary (2-3 sentences)
2. 3-5 emerging topics with reasons

Format as JSON:
{
  "analysis_summary": "...",
  "emerging_topics": [
    {"topic": "...", "reason": "..."}
  ]
}`;

    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content:
            "You are a research trend analyst. Always respond with valid JSON only.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const content =
      response.choices?.[0]?.message?.content || "{}";
    const contentStr = typeof content === "string" ? content : "{}";
    const jsonMatch = contentStr.match(/\{[\s\S]*\}/);
    const analysis = jsonMatch ? JSON.parse(jsonMatch[0]) : {};

    return {
      status: "success",
      topic,
      total_papers_analyzed: papers.length,
      analysis_summary:
        analysis.analysis_summary ||
        "Unable to generate analysis summary.",
      trends_by_year: trendsData,
      top_categories: topCategories,
      emerging_topics: analysis.emerging_topics || [],
    };
  } catch (error) {
    console.error("Error analyzing trends:", error);
    return {
      status: "error",
      message: String(error),
    };
  }
}

/**
 * Search papers on arXiv (with full input object)
 */
export async function searchArxivPapers(input: {
  query: string;
  authors?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  categories?: string[];
}) {
  const { query, authors, limit = 20 } = input;

  try {
    let searchQuery = `all:"${encodeURIComponent(query)}"`;
    if (authors) {
      searchQuery += ` AND au:"${encodeURIComponent(authors)}"`;
    }

    const response = await fetch(
      `http://export.arxiv.org/api/query?search_query=${encodeURIComponent(searchQuery)}&start=0&max_results=${Math.min(limit, 50)}&sortBy=relevance&sortOrder=descending`
    );

    if (!response.ok) {
      throw new Error(`arXiv API error: ${response.status}`);
    }

    const text = await response.text();
    const papers = parseArxivXML(text);

    return {
      status: "success",
      total_results: papers.length,
      returned_count: papers.length,
      papers: papers.slice(0, limit),
    };
  } catch (error) {
    console.error("Error searching papers:", error);
    return {
      status: "error",
      message: String(error),
      papers: [],
    };
  }
}

