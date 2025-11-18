import { getDynamicConfig } from "./config";

let awsJWT = none;

export async function checkAuth() {
    const config = await getDynamicConfig();

    // if logged in prior
    const savedToken = localStorage.getItem('cognito_tokens');
    if (savedToken) {
        awsJWT = JSON.parse(savedToken);
        return awsJWT;
    }

    // if just authed
    const params = new URLSearchParams(window.location.search);
    if (params.has('code')) {
        await getTokens(config, params.get('code'));
        return awsJWT;
    }

    // if not logged in
    redirectToLogin(config);
}

function redirectToLogin(config) {
    const homeUrl = encodeURIComponent(window.location.origin);
    const loginUrl = `${config.cognitoDomain}/login?` +
                     `client_id=${config.userPoolClientId}` +
                     `&response_type=code` +
                     `&scope=openid+email+profile` +
                     `&redirect_uri=${homeUrl}`;
    window.location.href = loginUrl;
}

async function getTokens(config, code) {
    const homeUrl = encodeURIComponent(window.location.origin);
    const body = `grant_type=authorization_code` +
                 `&client_id=${config.userPoolClientId}` +
                 `&code=${code}` +
                 `&redirect_uri=${homeUrl}`;
    
    const res = await fetch(`${config.cognitoDomain}/oauth2/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
    });

    if (!res.ok) {
        redirectToLogin(config);
        return;
    }

    awsJWT = await res.json();
    localStorage.setItem('cognito_tokens', JSON.stringify(awsJWT));
    window.history.replaceState({}, '', window.location.origin);
}

export function getIdToken() {
    if (!awsJWT) {
        const savedTokens = localStorage.getItem('cognito_tokens');
        if (savedTokens) {
            awsJWT = JSON.parse(savedTokens);
        }
    }
    return awsJWT?.id_token || "";
}

export async function signOut() {
    const config = await getDynamicConfig();

    localStorage.removeItem("cognito_tokens");
    const logoutUrl = `${config.cognitoDomain}/logout?` +
                      `client_id=${config.userPoolClientId}` +
                      `&logout_uri=${encodeURIComponent(window.location.origin)}`;
    
    window.location.href = logoutUrl;
}