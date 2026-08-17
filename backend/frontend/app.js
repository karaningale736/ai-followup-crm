const API_BASE = 'http://localhost:8000/api';

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function loadDashboard() {
  try {
    const dashboard = await fetchJson(`${API_BASE}/dashboard`);
    document.getElementById('total-clients').textContent = dashboard.total_clients;
    document.getElementById('due-today').textContent = dashboard.followups_due_today;
    document.getElementById('overdue').textContent = dashboard.overdue_followups;
    document.getElementById('meetings-today').textContent = dashboard.meetings_today;
    document.getElementById('agreements-pending').textContent = dashboard.agreements_pending;
    document.getElementById('api-status').textContent = 'Backend: online';
  } catch (error) {
    document.getElementById('api-status').textContent = 'Backend: offline';
    console.error(error);
  }
}

async function loadClients() {
  try {
    const clients = await fetchJson(`${API_BASE}/clients`);
    const table = document.getElementById('client-table-body');
    const select = document.getElementById('client-select');
    table.innerHTML = '';
    select.innerHTML = '';

    for (const client of clients) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="client-name">${client.first_name} ${client.last_name}</div>
          <div class="company-name">${client.email || '—'}</div>
        </td>
        <td class="company-name">${client.company_name || '—'}</td>
        <td><span class="badge">${client.current_stage || '—'}</span></td>
        <td><span class="badge ${client.priority.toLowerCase() || 'low'}">${client.priority || '—'}</span></td>
        <td>${client.last_contact_date || '—'}</td>
        <td><button class="client-action" data-client-id="${client.id}">Open</button></td>
      `;
      table.appendChild(tr);

      const option = document.createElement('option');
      option.value = client.id;
      option.textContent = `${client.first_name} ${client.last_name} - ${client.company_name}`;
      select.appendChild(option);
    }

    table.querySelectorAll('[data-client-id]').forEach((button) => {
      button.addEventListener('click', async () => {
        const id = Number(button.dataset.clientId);
        const selected = clients.find((client) => client.id === id);
        if (selected) {
          document.getElementById('selected-client-name').textContent = `${selected.first_name} ${selected.last_name}`;
          document.getElementById('selected-client-stage').textContent = `${selected.current_stage} • ${selected.company_name}`;
          document.getElementById('client-select').value = String(id);
          await analyzeClient(id);
        }
      });
    });
  } catch (error) {
    console.error(error);
  }
}

async function loadDue() {
  try {
    const due = await fetchJson(`${API_BASE}/followups/due`);
    const dueList = document.getElementById('due-list');
    dueList.innerHTML = '';

    if (!due.length) {
      dueList.innerHTML = '<div class="empty">No follow-ups due right now.</div>';
      return;
    }

    due.slice(0, 6).forEach((item) => {
      const div = document.createElement('div');
      div.className = 'due-item';
      div.innerHTML = `
        <div class="due-title">${item.client_name}</div>
        <div class="due-meta">${item.company_name} • ${item.stage} • ${item.priority}</div>
        <div class="due-meta">${item.recommended_action}</div>
      `;
      dueList.appendChild(div);
    });
  } catch (error) {
    console.error(error);
  }
}

async function analyzeClient(clientId) {
  const select = document.getElementById('client-select');
  const selectedId = clientId || Number(select.value);

  if (!selectedId) return;

  try {
    const payload = {
      client_id: selectedId
    };

    const response = await fetch(`${API_BASE}/followups/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status}`);
    }

    const result = await response.json();
    const output = document.getElementById('analysis-output');
    output.classList.remove('empty');
    output.innerHTML = `
      <strong>Recommended Action:</strong> ${result.recommended_action}<br/>
      <strong>Priority:</strong> ${result.priority}<br/>
      <strong>Template:</strong> ${result.template_category || '—'}<br/>
      <strong>Tone:</strong> ${result.tone}<br/>
      <strong>Reason:</strong> ${result.reason}
    `;

    await generateEmailPreview(selectedId, result.template_category);
  } catch (error) {
    console.error(error);
  }
}

async function generateEmailPreview(clientId, templateCategory) {
  try {
    const payload = {
      client_id: clientId,
      additional_variables: {}
    };

    const response = await fetch(`${API_BASE}/followups/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Generate failed: ${response.status}`);
    }

    const result = await response.json();
    const preview = document.getElementById('email-preview');
    preview.classList.remove('empty');
    preview.innerHTML = `
      <div><strong>Subject:</strong> ${result.subject}</div>
      <div class="email-body">${result.email_body}</div>
    `;
  } catch (error) {
    console.error(error);
    const preview = document.getElementById('email-preview');
    preview.classList.remove('empty');
    preview.textContent = 'Unable to generate a preview from the current API state.';
  }
}

async function init() {
  await loadDashboard();
  await loadClients();
  await loadDue();

  document.getElementById('refresh-button').addEventListener('click', async () => {
    await loadDashboard();
    await loadClients();
    await loadDue();
  });

  document.getElementById('analyze-button').addEventListener('click', async () => {
    const selectedId = Number(document.getElementById('client-select').value);
    await analyzeClient(selectedId);
  });

  const searchInput = document.getElementById('search-input');
  searchInput.addEventListener('input', async () => {
    const value = searchInput.value.trim().toLowerCase();
    if (!value) {
      await loadClients();
      return;
    }

    try {
      const clients = await fetchJson(`${API_BASE}/clients?search=${encodeURIComponent(value)}`);
      const table = document.getElementById('client-table-body');
      const select = document.getElementById('client-select');
      table.innerHTML = '';
      select.innerHTML = '';

      for (const client of clients) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><div class="client-name">${client.first_name} ${client.last_name}</div><div class="company-name">${client.email || '—'}</div></td>
          <td class="company-name">${client.company_name || '—'}</td>
          <td><span class="badge">${client.current_stage || '—'}</span></td>
          <td><span class="badge ${client.priority.toLowerCase() || 'low'}">${client.priority || '—'}</span></td>
          <td>${client.last_contact_date || '—'}</td>
          <td><button class="client-action" data-client-id="${client.id}">Open</button></td>
        `;
        table.appendChild(tr);

        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = `${client.first_name} ${client.last_name}`;
        select.appendChild(option);
      }
    } catch (error) {
      console.error(error);
    }
  });
}

init();
