const customerList = document.getElementById('customerList');
const customerForm = document.getElementById('customerForm');
const searchBtn = document.getElementById('searchBtn');
const searchInput = document.getElementById('searchInput');
const profileSection = document.getElementById('profileSection');
const profileContent = document.getElementById('profileContent');

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function getStatusClass(status) {
  const s = (status || '').toLowerCase();
  if (s === 'delivered') return 'delivered';
  if (s === 'ready') return 'ready';
  return 'pending';
}

async function loadCustomers(search = '') {
  const customers = await api(`/api/customers?search=${encodeURIComponent(search)}`);
  customerList.innerHTML = '';

  if (!customers.length) {
    customerList.innerHTML = '<p>No customers found.</p>';
    return;
  }

  customers.forEach((c) => {
    const item = document.createElement('div');
    item.className = 'customer-item';
    item.innerHTML = `
      <strong>${c.name}</strong><br/>
      📞 ${c.phone}<br/>
      <small>${c.address || ''}</small><br/>
      <button data-id="${c.id}">Open Profile</button>
    `;
    item.querySelector('button').addEventListener('click', () => openProfile(c.id));
    customerList.appendChild(item);
  });
}

function serializeForm(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  ['neck', 'chest', 'shoulder', 'sleeve_length', 'shirt_length', 'waist', 'hip', 'trouser_length'].forEach((key) => {
    if (data[key] === '') data[key] = null;
  });
  return data;
}

customerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const payload = serializeForm(customerForm);
    await api('/api/customers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    alert('Customer saved');
    customerForm.reset();
    await loadCustomers();
  } catch (err) {
    alert(err.message);
  }
});

searchBtn.addEventListener('click', () => loadCustomers(searchInput.value.trim()));

async function openProfile(customerId) {
  try {
    const detail = await api(`/api/customers/${customerId}`);
    const c = detail.customer;
    const m = detail.measurements || {};

    profileSection.classList.remove('hidden');
    profileContent.innerHTML = `
      <h3>${c.name}</h3>
      <p>📞 ${c.phone}<br/>🏠 ${c.address || ''}</p>

      <h4>Edit Customer Info</h4>
      <form id="editCustomerForm">
        <input name="name" value="${c.name}" required />
        <input name="phone" value="${c.phone}" required />
        <input name="address" value="${c.address || ''}" />
        <label>Date <input type="date" name="registration_date" value="${c.registration_date || ''}" required /></label>
        <textarea name="notes">${c.notes || ''}</textarea>
        <button type="submit">Update Customer</button>
      </form>

      <h4>Update Measurements</h4>
      <form id="measureForm" class="grid-2">
        <input name="neck" value="${m.neck ?? ''}" placeholder="Neck" type="number" step="0.1" />
        <input name="chest" value="${m.chest ?? ''}" placeholder="Chest" type="number" step="0.1" />
        <input name="shoulder" value="${m.shoulder ?? ''}" placeholder="Shoulder" type="number" step="0.1" />
        <input name="sleeve_length" value="${m.sleeve_length ?? ''}" placeholder="Sleeve Length" type="number" step="0.1" />
        <input name="shirt_length" value="${m.shirt_length ?? ''}" placeholder="Shirt Length" type="number" step="0.1" />
        <input name="waist" value="${m.waist ?? ''}" placeholder="Waist" type="number" step="0.1" />
        <input name="hip" value="${m.hip ?? ''}" placeholder="Hip" type="number" step="0.1" />
        <input name="trouser_length" value="${m.trouser_length ?? ''}" placeholder="Trouser Length" type="number" step="0.1" />
        <textarea name="additional_notes" placeholder="Measurement notes">${m.additional_notes || ''}</textarea>
        <button type="submit">Save Measurements</button>
      </form>

      <h4>Add Order</h4>
      <form id="orderForm">
        <input name="dress_type" placeholder="Dress type (Shalwar Kameez / Shirt / Pant)" required />
        <label>Delivery Date <input name="delivery_date" type="date" /></label>
        <input name="price" placeholder="Price" type="number" step="0.01" />
        <input name="advance_payment" placeholder="Advance Payment" type="number" step="0.01" />
        <select name="status">
          <option>Pending</option>
          <option>Ready</option>
          <option>Delivered</option>
        </select>
        <button type="submit">Save Order</button>
      </form>

      <h4>Orders</h4>
      <div id="ordersList">
        ${detail.orders.length ? detail.orders.map((o) => `
          <div class="customer-item">
            <strong>${o.dress_type}</strong> - <span class="badge ${getStatusClass(o.status)}">${o.status}</span><br/>
            Delivery: ${o.delivery_date || '-'}<br/>
            Price: ${o.price} | Advance: ${o.advance_payment} | Remaining: ${o.remaining_payment}
            <form class="orderUpdateForm" data-order-id="${o.id}">
              <select name="status">
                <option ${o.status === 'Pending' ? 'selected' : ''}>Pending</option>
                <option ${o.status === 'Ready' ? 'selected' : ''}>Ready</option>
                <option ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
              </select>
              <button type="submit">Update Status</button>
            </form>
            <form class="paymentForm" data-order-id="${o.id}">
              <input name="amount" type="number" step="0.01" placeholder="Payment amount" required />
              <button type="submit">Add Payment</button>
            </form>
          </div>
        `).join('') : '<p>No orders yet.</p>'}
      </div>

      <h4>Payment History</h4>
      <ul>
        ${detail.payments.length ? detail.payments.map((p) => `<li>${p.payment_date}: ${p.amount} (${p.dress_type})</li>`).join('') : '<li>No payments yet.</li>'}
      </ul>
    `;

    document.getElementById('editCustomerForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = serializeForm(e.target);
        await api(`/api/customers/${customerId}`, { method: 'PUT', body: JSON.stringify(payload) });
        alert('Customer updated');
        await loadCustomers(searchInput.value.trim());
        await openProfile(customerId);
      } catch (err) {
        alert(err.message);
      }
    });

    document.getElementById('measureForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = serializeForm(e.target);
        await api(`/api/customers/${customerId}/measurements`, { method: 'PUT', body: JSON.stringify(payload) });
        alert('Measurements updated');
        await openProfile(customerId);
      } catch (err) {
        alert(err.message);
      }
    });

    document.getElementById('orderForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const payload = serializeForm(e.target);
        await api(`/api/customers/${customerId}/orders`, { method: 'POST', body: JSON.stringify(payload) });
        alert('Order added');
        e.target.reset();
        await openProfile(customerId);
      } catch (err) {
        alert(err.message);
      }
    });

    document.querySelectorAll('.orderUpdateForm').forEach((form) => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderId = form.dataset.orderId;
        const status = new FormData(form).get('status');
        try {
          await api(`/api/orders/${orderId}`, { method: 'PUT', body: JSON.stringify({ status }) });
          alert('Order status updated');
          await openProfile(customerId);
        } catch (err) {
          alert(err.message);
        }
      });
    });

    document.querySelectorAll('.paymentForm').forEach((form) => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderId = form.dataset.orderId;
        const amount = new FormData(form).get('amount');
        try {
          await api(`/api/orders/${orderId}/payments`, { method: 'POST', body: JSON.stringify({ amount }) });
          alert('Payment added');
          await openProfile(customerId);
        } catch (err) {
          alert(err.message);
        }
      });
    });
  } catch (err) {
    alert(err.message);
  }
}

loadCustomers();
