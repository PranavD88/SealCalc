import { useEffect, useState } from "react";

type Options = {
  eyes: number[];
  mouth: number[];
  hair: number[];
  pattern: number[];
  color: number[];
};

type PreviewUrls = {
  layers: string[];
  urls: Record<string, string>;
};

const API = import.meta.env.VITE_API_BASE || "";

export default function App() {
  const [opts, setOpts] = useState<Options | null>(null);

  const [eyes, setEyes] = useState(1);
  const [mouth, setMouth] = useState(1);
  const [hair, setHair] = useState(0);
  const [pattern, setPattern] = useState(1);
  const [baseColor, setBaseColor] = useState(1);
  const [patternColor, setPatternColor] = useState(1);

  const [preview, setPreview] = useState<PreviewUrls | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const r = await fetch(`${API}/options`);
      if (!r.ok) return;
      const data: Options = await r.json();
      setOpts(data);
      setEyes(data.eyes[0]);
      setMouth(data.mouth[0]);
      setHair(data.hair[0]);
      setPattern(data.pattern[0]);
      setBaseColor(data.color[0]);
      setPatternColor(data.color[0]);
    })();
  }, []);

  async function doPreview() {
    const payload = {
      eyes,
      mouth,
      hair,
      pattern,
      base_color: baseColor,
      pattern_color: patternColor,
    };
    const r = await fetch(`${API}/preview-urls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) return;
    const data: PreviewUrls = await r.json();
    setPreview(data);
  }

  async function saveSeal() {
    setSaving(true);
    const payload = {
      timestamp: new Date().toISOString(),
      eyes,
      mouth,
      hair,
      pattern,
      base_color: baseColor,
      pattern_color: patternColor,
    };
    const r = await fetch(`${API}/submit-seal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSaving(false);
    if (!r.ok) {
      alert("Save failed");
      return;
    }
    const data = await r.json();
    alert(`Saved! Seal ID: ${data.id}`);
  }

  if (!opts) return <p style={{ padding: 16 }}>Loading options…</p>;

  return (
    <div style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h2>SealCalc Builder</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(220px, 1fr))",
          gap: 12,
          maxWidth: 900,
        }}
      >
        <Select label="Eyes" value={eyes} onChange={setEyes} options={opts.eyes} />
        <Select label="Mouth" value={mouth} onChange={setMouth} options={opts.mouth} />
        <Select label="Hair (0=none)" value={hair} onChange={setHair} options={opts.hair} />
        <Select label="Pattern" value={pattern} onChange={setPattern} options={opts.pattern} />
        <Select label="Base Color" value={baseColor} onChange={setBaseColor} options={opts.color} />
        <Select label="Pattern Color" value={patternColor} onChange={setPatternColor} options={opts.color} />
      </div>

      <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
        <button onClick={doPreview}>Preview</button>
        <button onClick={saveSeal} disabled={saving}>
          {saving ? "Saving…" : "Save to DB"}
        </button>
      </div>

      <div
        style={{
          marginTop: 16,
          position: "relative",
          width: 280,
          height: 280,
          border: "1px solid #ddd",
          borderRadius: 12,
        }}
      >
        {preview?.layers.map((k, i) => {
          const url = preview.urls[k];
          if (!url) return null;
          return (
            <img
              key={k}
              src={url}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 10 + i }}
            />
          );
        })}
      </div>
    </div>
  );
}

function Select<T extends string | number>({
  label,
  value,
  onChange,
  options,
  parse,
}: {
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: readonly T[] | T[];
  parse?: (raw: string) => T;
}) {
  return (
    <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <span style={{ minWidth: 130 }}>{label}</span>
      <select
        value={String(value)}
        onChange={(e) => {
          const raw = e.target.value;
          const next = parse ? parse(raw) : (typeof value === "number" ? (Number(raw) as T) : (raw as T));
          onChange(next);
        }}
      >
        {options.map((o) => (
          <option key={String(o)} value={String(o)}>
            {String(o)}
          </option>
        ))}
      </select>
    </label>
  );
}
