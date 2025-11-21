import { getDynamicConfig } from "./config";
import { getIdToken } from "./auth";

async function getApiBase() {
    const config = await getDynamicConfig();
    return (config.apiBase).trim();
}

export async function createOrder(data) {
    const api = await getApiBase();
    const token = getIdToken();

    const res = await fetch(api, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer ' + token,
        },
        body: JSON.stringify(data),
    });

    const dataString = await res.text();
    let parsed = JSON.parse(dataString || '{}');

    return parsed;
}

export async function listOrders() {
    const api = await getApiBase();
    const token = getIdToken();

    const res = await fetch(api, {
        headers: { Authorization: 'Bearer ' + token },
    });

    let body = await res.text();
    let data = {};
    try {
        data = JSON.parse(body || '{}')
    } catch {
        data = {};
    }

    if (!res.ok) {
        throw { error: data.error };
    } 

    return data;
}

export async function getOrderById(id) {
    const api = await getApiBase();
    const token = getIdToken();

    const res = await fetch(`${api}/${encodeURIComponent(id)}`, {
        headers: { Authorization: 'Bearer ' + token},
    });

    let body = await res.text();
    let data = {};
    try {
        data = JSON.parse(body || '{}');
    } catch {
        data = {};
    }

    if (res.status === 404) {
        return {error: 'Order not found'};
    }
    if (!res.ok) {
        return { error: data.error }
    }
    return data;
}