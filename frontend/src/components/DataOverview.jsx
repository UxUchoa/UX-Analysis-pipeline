import { Database, Columns, Hash, FilterX } from 'lucide-react';
import MetricCard from './MetricCard';
import DataTable from './DataTable';
import { useLanguage } from '../i18n';

export default function DataOverview({ uploadData }) {
  const { t } = useLanguage();
  if (!uploadData) return null;

  return (
    <div className="animate-fade-in">
      <div className={uploadData.excluded_rows ? 'grid-4' : 'grid-3'} style={{ marginBottom: 'var(--space-xl)' }}>
        <MetricCard
          icon={<Database size={18} />}
          value={uploadData.rows}
          label={t.total_records}
          className="stagger-1"
        />
        <MetricCard
          icon={<Columns size={18} />}
          value={uploadData.columns}
          label={t.columns}
          className="stagger-2"
        />
        <MetricCard
          icon={<Hash size={18} />}
          value={Object.keys(uploadData.data_types || {}).length}
          label={t.data_types}
          className="stagger-3"
        />
        {!!uploadData.excluded_rows && (
          <MetricCard
            icon={<FilterX size={18} />}
            value={uploadData.excluded_rows}
            label={t.excluded_records}
            className="stagger-4"
          />
        )}
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <h2>{t.raw_data}</h2>
        </div>
        <DataTable data={uploadData.data} maxRows={50} />
      </div>

      {uploadData.summary && uploadData.summary.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2>{t.summary}</h2>
          </div>
          <DataTable data={uploadData.summary} />
        </div>
      )}
    </div>
  );
}
