const { IgApiClient } = require('instagram-private-api');
const { withFbns } = require('instagram_mqtt');
const fs = require('fs').promises;
const path = require('path');
const http = require('http');

(async () => {
    const ig = withFbns(new IgApiClient());
    const API_BASE_URL = 'http://localhost:8000/api/v1';
    const NOTIFICATIONS_ENDPOINT = `${API_BASE_URL}/notifications`;

    // Function to send HTTP POST request
    const sendNotification = async (data) => {
        return new Promise((resolve, reject) => {
            const postData = JSON.stringify({ notification: data });

            const options = {
                hostname: 'localhost',
                port: 8000,
                path: '/notifications',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };

            const req = http.request(options, (res) => {
                let responseData = '';
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                res.on('end', () => {
                    console.log(`Notification sent successfully: ${res.statusCode} - ${responseData}`);
                    resolve({ statusCode: res.statusCode, body: responseData });
                });
            });

            req.on('error', (error) => {
                console.error('Error sending notification:', error.message);
                reject(error);
            });

            req.write(postData);
            req.end();
        });
    };

    // Function to load and set up session
    async function loadAndSetupSession(ig, retryCount = 0) {
        const maxRetries = 1;
        const sessionPath = path.join(__dirname, '..', 'credentials.json');

        try {
            // Load credentials.json
            const data = await fs.readFile(sessionPath, 'utf8');
            if (!data) {
                throw new Error('credentials.json is empty');
            }
            const credentials = JSON.parse(data);
            const session = credentials.session;
            if (!session) {
                throw new Error('No "session" key in credentials.json');
            }
            console.log('Loaded session from credentials.json');

            // Extract username (using ds_user_id as fallback)
            const username = session?.authorization_data?.ds_user_id || 'unknown_user';
            console.log(`Setting up session for username: ${username}`);

            // Set basic data
            ig.state.generateDevice(username);
            ig.state.userAgent = session.user_agent;

            // Set cookies
            const sessionid = session.authorization_data.sessionid;
            const ds_user_id = session.authorization_data.ds_user_id;
            const mid = session.mid;
            await ig.state.cookieJar.setCookie(
                `sessionid=${sessionid}; Domain=.instagram.com; Path=/; Secure; HttpOnly`,
                'https://www.instagram.com'
            );
            await ig.state.cookieJar.setCookie(
                `ds_user_id=${ds_user_id}; Domain=.instagram.com; Path=/; Secure; HttpOnly`,
                'https://www.instagram.com'
            );
            await ig.state.cookieJar.setCookie(
                `mid=${mid}; Domain=.instagram.com; Path=/; Secure; HttpOnly`,
                'https://www.instagram.com'
            );
            console.log('Set sessionid:', sessionid);
            console.log('Set ds_user_id:', ds_user_id);
            console.log('Set mid:', mid);

            return session;
        } catch (e) {
            console.error('Session setup error:', e.message);
            if (retryCount >= maxRetries) {
                console.error('Max retries reached, exiting');
                return null;
            }
            // If session fails, you might want to handle re-authentication logic here
            // For now, just retry once without external signaling
            console.log('Retrying session setup...');
            return await loadAndSetupSession(ig, retryCount + 1);
        }
    }

    // Load and set up session
    const session = await loadAndSetupSession(ig);
    if (!session) {
        console.error('Failed to set up session, exiting');
        return;
    }

    // Listen for Instagram notifications
    ig.fbns.on('push', async (data) => {
        console.log('Instagram notification:', data);
        try {
            await sendNotification(data);
        } catch (error) {
            console.error('Failed to send notification:', error.message);
        }
    });

    ig.fbns.on('error', (error) => console.error('FBNS error:', error));
    ig.fbns.on('warning', (warning) => console.warn('FBNS warning:', warning));
    ig.fbns.on('connect', () => console.log('Connected to FBNS!'));

    // Connect to FBNS
    try {
        await ig.fbns.connect({
            connectOverrides: {
                host: 'mqtt-mini.facebook.com',
                port: 443,
                protocol: 'mqtt',
                family: 4 // Force IPv4
            }
        });
        console.log('Waiting for notifications...');
    } catch (e) {
        console.error('FBNS connection error:', e.message);
        console.error('Error details:', e);
    }
})();