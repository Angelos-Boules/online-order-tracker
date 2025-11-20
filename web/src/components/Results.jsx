function Results({ single, list }) {
    const extract = (f) => f?.S || f?.N || '';

    const formatDate = (raw) => {
        if (!raw) return "";
        const formatted = new Date(raw);
        return formatted.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    return (
        <div className='container mt-4'>
        {single && (
        <div className='table-responsive mb-4'>
            <table className='table table-dark table-striped table-bordered'>
            <thead>
                <tr>
                    <th colSpan={2}>Order: {extract(single.orderId)}</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Name</td>
                    <td>{extract(single.name)}</td>
                </tr>
                <tr>
                    <td>Product</td>
                    <td>{extract(single.product)}</td>
                </tr>
                <tr>
                    <td>Email</td>
                    <td>{extract(single.email)}</td>
                </tr>
                <tr>
                    <td>Created At</td>
                    <td>{formatDate(extract(single.createdAt))}</td>
                </tr>                
            </tbody>
          </table>
        </div>
      )}

      {list && list.length > 0 && (
        <div className='table-responsive'>
          <table className='table table-dark table-striped table-bordered'>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Name</th>
                <th>Product</th>
                <th>Email</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {list.map((o) => (
                <tr key={extract(o.orderId)}>
                  <td>{extract(o.orderId)}</td>
                  <td>{extract(o.name)}</td>
                  <td>{extract(o.product)}</td>
                  <td>{extract(o.email)}</td>
                  <td>{formatDate(extract(o.createdAt))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
}

export default Results;
