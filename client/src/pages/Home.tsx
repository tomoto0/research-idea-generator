import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { APP_TITLE } from "@/const";

export default function Home() {
  const [activeTab, setActiveTab] = useState("ideas");
  const [topic, setTopic] = useState("");
  const [focusArea, setFocusArea] = useState("");
  const [numPapers, setNumPapers] = useState(10);
  const [trendTopic, setTrendTopic] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any>(null);
  const [trendResults, setTrendResults] = useState<any>(null);
  const [ideaResults, setIdeaResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const generateIdeasMutation = trpc.research.generateIdeas.useMutation();
  const analyzeTrendsMutation = trpc.research.analyzeTrends.useMutation();
  const searchPapersMutation = trpc.research.searchPapers.useMutation();

  const handleGenerateIdeas = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const result = await generateIdeasMutation.mutateAsync({
        topic,
        focus_area: focusArea,
        num_papers: numPapers,
        categories: [],
      });
      setIdeaResults(result);
    } catch (error) {
      console.error("Error generating ideas:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeTrends = async () => {
    if (!trendTopic.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeTrendsMutation.mutateAsync({
        topic: trendTopic,
        time_range: "past_3_years",
        num_papers: 300,
        categories: [],
      });
      setTrendResults(result);
    } catch (error) {
      console.error("Error analyzing trends:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchPapers = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const result = await searchPapersMutation.mutateAsync({
        query: searchQuery,
        limit: 20,
      });
      setSearchResults(result);
    } catch (error) {
      console.error("Error searching papers:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">🔬 {APP_TITLE}</h1>
          <p className="text-gray-600">AI-powered research idea generation with arXiv integration</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="ideas">💡 Idea Generation</TabsTrigger>
            <TabsTrigger value="trends">📈 Trend Analysis</TabsTrigger>
            <TabsTrigger value="search">🔍 Paper Search</TabsTrigger>
          </TabsList>

          <TabsContent value="ideas">
            <Card>
              <CardHeader>
                <CardTitle>Research Idea Generation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Research topic (e.g., quantum computing, AI ethics)"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                />
                <Input
                  placeholder="Focus area (optional)"
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                />
                <Input
                  type="number"
                  placeholder="Number of papers"
                  value={numPapers}
                  onChange={(e) => setNumPapers(parseInt(e.target.value))}
                  min="5"
                  max="50"
                />
                <Button onClick={handleGenerateIdeas} disabled={loading} className="w-full">
                  {loading ? "Generating..." : "🚀 Generate Ideas"}
                </Button>
                {ideaResults && (
                  <div className="mt-6 space-y-4">
                    {ideaResults.success && ideaResults.ideas?.map((idea: any, idx: number) => (
                      <Card key={idx} className="border-l-4 border-blue-500">
                        <CardHeader>
                          <CardTitle className="text-lg">{idea.title}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          {idea.overview?.background && (
                            <p><strong>Background:</strong> {idea.overview.background}</p>
                          )}
                          {idea.methodology?.research_design && (
                            <p><strong>Methodology:</strong> {idea.methodology.research_design}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends">
            <Card>
              <CardHeader>
                <CardTitle>Research Trend Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Research topic"
                  value={trendTopic}
                  onChange={(e) => setTrendTopic(e.target.value)}
                />
                <Button onClick={handleAnalyzeTrends} disabled={loading} className="w-full">
                  {loading ? "Analyzing..." : "📊 Analyze Trends"}
                </Button>
                {trendResults && (
                  <div className="mt-6 space-y-4">
                    {trendResults.status === "success" && (
                      <>
                        <div className="p-4 bg-blue-50 rounded">
                          <p className="text-sm">{trendResults.analysis_summary}</p>
                        </div>
                        {trendResults.emerging_topics?.map((topic: any, idx: number) => (
                          <div key={idx} className="p-3 bg-green-50 rounded">
                            <p className="font-semibold">{topic.topic}</p>
                            <p className="text-sm text-gray-600">{topic.reason}</p>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="search">
            <Card>
              <CardHeader>
                <CardTitle>Paper Search</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Search query"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Button onClick={handleSearchPapers} disabled={loading} className="w-full">
                  {loading ? "Searching..." : "🔎 Search Papers"}
                </Button>
                {searchResults && (
                  <div className="mt-6 space-y-4">
                    {searchResults.status === "success" && searchResults.papers?.map((paper: any, idx: number) => (
                      <Card key={idx} className="border-l-4 border-green-500">
                        <CardHeader>
                          <CardTitle className="text-base">{paper.title}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <p><strong>Date:</strong> {paper.date}</p>
                          <p><strong>Categories:</strong> {paper.categories?.join(", ")}</p>
                          <p className="text-gray-600">{paper.abstract?.substring(0, 200)}...</p>
                          <a href={paper.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                            View on arXiv →
                          </a>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
