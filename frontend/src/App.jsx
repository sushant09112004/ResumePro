import { useState } from "react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const res = await fetch("http://localhost:8000/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: query, top_k: 5 })
    });
    const data = await res.json();
    setResults(data.results);
  };

  return (
    <div className="p-4">
      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search..." />
      <button onClick={handleSearch}>Search</button>
      <div>
        {results.map((r, i) => (
          <div key={i} className="border p-2 my-2">
            <p><strong>Score:</strong> {r.score.toFixed(3)}</p>
            <p>{r.text}</p>
          </div>
        ))}
      </div>
      <div>
      </div>
    </div>
  );
}
