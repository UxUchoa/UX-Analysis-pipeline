import { Download } from 'lucide-react';
import { getExportUrl } from '../api';
import { useLanguage } from '../i18n';

export default function ExportPanel({ hasReport }) {
  const { t } = useLanguage();

  return (
    <div className="animate-fade-in">
      <div className="grid-3">
        <a href={getExportUrl('csv')} className="btn btn-secondary btn-full" style={{ textDecoration: 'none' }}>
          <Download size={16} />
          {t.download_csv}
        </a>
        <a href={getExportUrl('excel')} className="btn btn-secondary btn-full" style={{ textDecoration: 'none' }}>
          <Download size={16} />
          {t.download_excel}
        </a>
        {hasReport && (
          <a href={getExportUrl('report')} className="btn btn-secondary btn-full" style={{ textDecoration: 'none' }}>
            <Download size={16} />
            {t.download_json}
          </a>
        )}
      </div>
    </div>
  );
}
