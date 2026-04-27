import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { useLanguage } from '../i18n';

const CHART_COLORS = ['#7c5cfc', '#5b8def', '#2ed573', '#ff7f50', '#ff4757', '#ffa502'];

export default function QuantitativePanel({ data }) {
  const { t } = useLanguage();
  const quantData = data?.quantitative;
  if (!quantData) return <div className="empty-state"><h3>{t.no_data}</h3></div>;

  const numericCols = quantData.numeric ? Object.keys(quantData.numeric) : [];
  const catCols = quantData.categorical ? Object.keys(quantData.categorical) : [];

  // Build histogram-style data for numeric columns
  const histogramData = useMemo(() => {
    const result = {};
    numericCols.forEach(col => {
      const values = quantData.numeric[col].values;
      if (!values || values.length === 0) return;
      const min = Math.min(...values);
      const max = Math.max(...values);
      const bins = 12;
      const binWidth = (max - min) / bins || 1;
      const buckets = Array.from({ length: bins }, (_, i) => ({
        range: `${(min + i * binWidth).toFixed(0)}-${(min + (i + 1) * binWidth).toFixed(0)}`,
        count: 0,
      }));
      values.forEach(v => {
        const idx = Math.min(Math.floor((v - min) / binWidth), bins - 1);
        buckets[idx].count++;
      });
      result[col] = buckets;
    });
    return result;
  }, [numericCols, quantData]);

  return (
    <div className="animate-fade-in">
      {/* Numeric distributions */}
      {numericCols.map(col => (
        <div key={col} className="chart-container">
          <h3 className="chart-title"><BarChart3 size={18} /> {col}</h3>
          <p className="chart-caption">
            Média: {quantData.numeric[col].mean?.toFixed(1)} | 
            Min: {quantData.numeric[col].min} | 
            Max: {quantData.numeric[col].max} | 
            Mediana: {quantData.numeric[col].median?.toFixed(1)}
          </p>
          {histogramData[col] && (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={histogramData[col]}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="range" tick={{ fill: '#8b8b9e', fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                <Bar dataKey="count" fill="#7c5cfc" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      ))}

      {/* Categorical distributions */}
      {catCols.length > 0 && (
        <>
          <h2 style={{ margin: 'var(--space-xl) 0 var(--space-md)', fontSize: 'var(--font-size-xl)' }}>
            {t.categorical_dist}
          </h2>
          <div className="grid-2">
            {catCols.map(col => (
              <div key={col} className="chart-container">
                <h3>{col}</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={quantData.categorical[col]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {quantData.categorical[col].map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
