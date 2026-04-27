import { useState, useCallback } from 'react';
import { Upload, CheckCircle, RefreshCw } from 'lucide-react';
import { useLanguage } from '../i18n';

export default function FileUpload({ onFileSelected, isLoaded, filename }) {
  const { t } = useLanguage();
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onFileSelected(file);
  }, [onFileSelected]);

  const handleChange = useCallback((e) => {
    const file = e.target.files[0];
    if (file) onFileSelected(file);
    e.target.value = '';
  }, [onFileSelected]);

  return (
    <div className="file-upload-stack">
      {isLoaded && filename && (
        <div className="file-loaded animate-fade-in">
          <CheckCircle size={16} />
          <span>{filename}</span>
        </div>
      )}
      <label
        className={`file-upload-zone ${isLoaded ? 'compact' : ''} ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        {isLoaded ? <RefreshCw size={18} className="upload-icon" /> : <Upload size={28} className="upload-icon" />}
        <p>{isLoaded ? 'Enviar outra tabela' : t.upload_help}</p>
        <span className="file-types">.xlsx, .xls, .csv</span>
      </label>
    </div>
  );
}
