let config = null;

export async function getDynamicConfig() {
    if (config) return config;
    const res = await fetch("/config.json", { cache: "no-store" });
    config = await res.json();
    return config;
}
