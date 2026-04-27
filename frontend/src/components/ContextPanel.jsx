import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import MetricCard from './MetricCard';
import { useLanguage } from '../i18n';
import { Users, Calendar, Clock, Building2, Star, MessageSquareText } from 'lucide-react';

const CHART_COLORS = ['#7c5cfc', '#5b8def', '#2ed573', '#ff7f50', '#ff4757', '#ffa502', '#a78bfa', '#34e7e4'];

export default function ContextPanel({ data }) {
  const { t } = useLanguage();
  const ctxData = data?.context;
  if (!ctxData) return <div className="empty-state"><h3>{t.no_data}</h3></div>;

  const profiles = ctxData.profiles || [];
  const ratings = ctxData.ratings || [];
  const themes = ctxData.themes || [];

  // Compute metrics
  const metrics = useMemo(() => {
    const ages = profiles.map(p => p.age).filter(v => v != null);
    const timeBb = profiles.map(p => p.time_bb).filter(v => v != null);
    const timeTeam = profiles.map(p => p.time_team).filter(v => v != null);
    const uniqueParticipants = new Set(profiles.map(p => p.participant)).size;
    return {
      participants: uniqueParticipants,
      avgAge: ages.length ? (ages.reduce((a, b) => a + b, 0) / ages.length).toFixed(1) : 'N/A',
      avgTimeBb: timeBb.length ? (timeBb.reduce((a, b) => a + b, 0) / timeBb.length).toFixed(1) : 'N/A',
      avgTimeTeam: timeTeam.length ? (timeTeam.reduce((a, b) => a + b, 0) / timeTeam.length).toFixed(1) : 'N/A',
    };
  }, [profiles]);

  // Team distribution
  const teamData = useMemo(() => {
    const counts = {};
    profiles.forEach(p => {
      const team = p.team || 'Não informado';
      counts[team] = (counts[team] || 0) + 1;
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, [profiles]);

  // Sex/gender distribution
  const genderData = useMemo(() => {
    const counts = {};
    profiles.forEach(p => {
      if (!p.gender) return;
      const gender = p.gender || 'Não informado';
      counts[gender] = (counts[gender] || 0) + 1;
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, [profiles]);

  // Ratings by question
  const ratingData = useMemo(() => {
    if (!ratings.length) return [];
    const byQ = {};
    ratings.forEach(r => {
      if (!byQ[r.question]) byQ[r.question] = [];
      byQ[r.question].push(r.rating);
    });
    return Object.entries(byQ).map(([q, vals]) => ({
      question: q,
      average: (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1),
    }));
  }, [ratings]);

  return (
    <div className="animate-fade-in">
      {/* Metrics */}
      <div className="grid-4" style={{ marginBottom: 'var(--space-xl)' }}>
        <MetricCard icon={<Users size={18} />} value={metrics.participants} label={t.participants} className="stagger-1" />
        <MetricCard icon={<Calendar size={18} />} value={metrics.avgAge} label={t.avg_age} className="stagger-2" />
        <MetricCard icon={<Clock size={18} />} value={metrics.avgTimeBb} label={t.avg_time_bb} className="stagger-3" />
        <MetricCard icon={<Building2 size={18} />} value={metrics.avgTimeTeam} label={t.avg_time_team} className="stagger-4" />
      </div>

      {/* Team Distribution */}
      {teamData.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title"><Building2 size={18} /> {t.team_dist}</h3>
          <div className="grid-2">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={teamData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                  {teamData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
              </PieChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={teamData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                <Bar dataKey="count" fill="#7c5cfc" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Sex/Gender Distribution */}
      {genderData.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title"><Users size={18} /> {t.gender_dist}</h3>
          <div className="grid-2">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={genderData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                  {genderData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
              </PieChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={genderData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                <YAxis tick={{ fill: '#8b8b9e', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
                <Bar dataKey="count" fill="#5b8def" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Ratings */}
      {ratingData.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title"><Star size={18} /> {t.ratings_title}</h3>
          <ResponsiveContainer width="100%" height={Math.max(200, ratingData.length * 50)}>
            <BarChart data={ratingData} layout="vertical" margin={{ left: 200 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" domain={[0, 5]} tick={{ fill: '#8b8b9e', fontSize: 12 }} />
              <YAxis type="category" dataKey="question" tick={{ fill: '#f0f0f5', fontSize: 11 }} width={190} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }} />
              <Bar dataKey="average" name="Média" fill="#ffa502" radius={[0, 4, 4, 0]}>
                {ratingData.map((entry, i) => (
                  <Cell key={i} fill={entry.average >= 4 ? '#2ed573' : entry.average >= 3 ? '#ffa502' : '#ff4757'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Themes */}
      {themes.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title"><MessageSquareText size={18} /> {t.themes_title}</h3>
          <ResponsiveContainer width="100%" height={Math.max(200, themes.length * 50)}>
            <BarChart data={themes} layout="vertical" margin={{ left: 150 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tick={{ fill: '#8b8b9e', fontSize: 12 }} />
              <YAxis type="category" dataKey="theme" tick={{ fill: '#f0f0f5', fontSize: 12 }} width={140} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#f0f0f5' }}
                formatter={(val, name) => name === 'percentage' ? `${val}%` : val} />
              <Bar dataKey="occurrences" name="Ocorrências" fill="#5b8def" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
