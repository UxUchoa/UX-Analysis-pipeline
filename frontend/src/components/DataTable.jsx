export default function DataTable({ data, maxRows = 100 }) {
  if (!data || data.length === 0) return null;
  const columns = Object.keys(data[0]);
  const rows = data.slice(0, maxRows);

  return (
    <div className="data-table-wrapper data-table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col} title={String(row[col] ?? '')}>
                  {row[col] != null ? String(row[col]) : ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
