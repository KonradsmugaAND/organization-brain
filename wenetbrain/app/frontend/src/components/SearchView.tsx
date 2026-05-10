import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, type SearchResult } from "@/api";

interface SearchViewProps {
  query: string;
}

export function SearchView({ query }: SearchViewProps) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    apiGet<SearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`)
      .then(setResults)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [query]);

  if (loading) {
    return <div className="p-5 text-sm" style={{ color: "var(--color-text-tertiary)" }}>Szukanie...</div>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>Wyniki wyszukiwania</h2>
        <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>„{query}”</p>
      </div>

      {results.length === 0 && (
        <div className="text-center py-12" style={{ color: "var(--color-text-tertiary)" }}>
          <span className="material-icons-outlined text-5xl mb-3 opacity-40">search</span>
          <div className="text-sm font-semibold" style={{ color: "var(--color-text-secondary)" }}>Brak wyników</div>
          <div className="text-xs mt-1">Spróbuj innego zapytania</div>
        </div>
      )}

      <div className="space-y-3">
        {results.map((r, i) => (
          <Card key={i} className="border" style={{ background: "var(--color-background-secondary)", borderColor: "var(--color-border-primary)", borderRadius: "var(--radius-lg)" }}>
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center gap-2">
                <Badge className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "color-mix(in oklch, var(--color-accent) 15%, transparent)", color: "var(--color-accent)" }}>
                  {r.bank_id}
                </Badge>
                <Badge variant="outline" className="text-[11px]" style={{ borderColor: "var(--color-border-primary)", color: "var(--color-text-tertiary)" }}>
                  score: {r.score?.toFixed(2)}
                </Badge>
              </div>
              <div className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                {r.payload?.title || r.payload?.chunk_text?.substring(0, 60) || "Notatka"}
              </div>
              <div className="text-[13px]" style={{ color: "var(--color-text-secondary)" }}>
                {r.payload?.chunk_text}
              </div>
              <div className="flex items-center gap-3 text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
                <span>{r.payload?.meeting_title || r.payload?.user_id}</span>
                <span>{r.payload?.meeting_date || r.payload?.created_at?.substring(0, 10)}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
