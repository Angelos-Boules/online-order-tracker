function OrderCard({ form, setForm, onCreate, status, orderId, setOrderId, 
    onGetOrder, onList, oneStatus, listStatus 
}) {
    return (
        <div className='card bg-dark text-light p-4 shadow mx-auto' style={{ maxWidth: '400px'}}>
            <h3 className='mb-3 text-center text-white'>Place an Order</h3>

            <form onSubmit={onCreate}>
                <div className='mb-3'>
                <label className='form-label text-light'> Name </label>
                    <input
                        className='form-control'
                        type='text'
                        required
                        value={form.name}
                        onChange={(event) => setForm({...form, name: event.target.value })}
                    />
                </div>

                <div className='mb-3'>
                    <label className='form-label text-light'> Product </label>
                        <input
                            className='form-control'
                            type='text'
                            required
                            value={form.product}
                            onChange={(event) => setForm({...form, product: event.target.value })}
                        />
                </div>

                <div className="mb-3">
                    <label className="form-label text-light"> Email </label>
                        <input
                            className='form-control'
                            type='text'
                            required
                            value={form.email}
                            onChange={(event) => setForm({...form, email: event.target.value })}
                        />
                </div>
                <button type='submit' className='btn btn-light my-4 w-100'> Submit Order </button>
            </form>

            { status && <p className='text-center mt-2 text-info'>{status}</p> }

            <div className='text-center my-4'>- OR -</div>

            <h5 className='text-white'> Find Order </h5>
            <form className='d-flex gap-2 mb-2' onSubmit={onGetOrder}>
                <input
                    className='form-control'
                    type='text'
                    placeholder='Order ID'
                    value={orderId}
                    onChange={(e) => setOrderId(e.target.value)}
                />
                <button className='btn btn-outline-light' type='submit'>
                    Search
                </button>
            </form>

            {oneStatus && <p className='text-center text-warning'>{oneStatus}</p>}

            <h5 className='mt-4 text-white'>View All Orders</h5>
            <button className="mt-1 btn btn-outline-light w-100" onClick={onList}>
                View All Orders
            </button>
            {listStatus && <p className="status-text">{listStatus}</p>}
        </div>
    );
};

export default OrderCard;