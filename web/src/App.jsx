import { useState } from 'react';
import Navbar from './components/Navbar';
import OrderCard from './components/OrderCard';
import Results from './components/Results';

import { createOrder, listOrders, getOrderById } from './api';
import './App.css';

function App() {
  const [productSubmit, setProductSubmit] = useState({ name: '', product: '', email: ''}); // Submission Form 
  const [createStatus, setCreateStatus] = useState(''); // Submit status message

  const [orderId, setOrderId] = useState(''); // Order id
  const [getOneStatus, setGetOneStatus] = useState(''); // Order Id submission status
  const [order, setOrder] = useState(null); // Order from api

  const [allOrders, setAllOrders] = useState([]); // Orders from api
  const [allOrdersStatus, setAllOrdersStatus] = useState(''); // list of orders status

  async function handleCreate(event) {
    event.preventDefault();
    setOrder(null);
    setAllOrders([]);

    const res = await createOrder(productSubmit);
    if (res.error) {
      setCreateStatus(res.error);
    } else {
      setCreateStatus(`Submitted! Order ID: ${res.orderId}`);
      setProductSubmit({ name: '', product: '', email: ''});
    }
  }

  async function handleOneOrder(event) {
    event.preventDefault();
    if (!orderId) return;

      setOrder(null);
      setAllOrders([]);

      const data = await getOrderById(orderId);
      if (data.error) {
        setGetOneStatus(data.error);
      } else {
        setGetOneStatus('');
        setOrder(data.order);
      }
  }

  async function handleAllOrders() {
    setOrder(null);

    const data = await listOrders();
    if (data.error) {
      setAllOrdersStatus(data.error);
    } else {
      setAllOrdersStatus('');
      setAllOrders(data.orders)
    }
  }

  return (
  <>
    <Navbar />

    <main className='container mt-4'>
      <div className='row g-4'>

        <div className='col-12 col-md-4'>
          <OrderCard
            form={productSubmit}
            setForm={setProductSubmit}
            onCreate={handleCreate}
            status={createStatus}
            orderId={orderId}
            setOrderId={setOrderId}
            onGetOrder={handleOneOrder}
            onList={handleAllOrders}
            oneStatus={getOneStatus}
            listStatus={allOrdersStatus}
          />
        </div>

        <div className='col-12 col-md-8'>
          <Results single={order} list={allOrders} />
        </div>
      </div>
    </main>
  </>
  );
}

export default App;
